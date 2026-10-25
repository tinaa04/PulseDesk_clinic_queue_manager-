`from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3, uuid, os
from datetime import datetime, date
from pathlib import Path
from core.queue_manager import QueueManager, PRIORITY
from core.triage import CATEGORIES, validate_category
from core.patient_search import search_patients

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get("PULSEDESK_SECRET", "local-demo-change-me")
DB_PATH = ROOT / "database" / "pulsedesk.db"
queue = QueueManager()

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn=db()
    conn.executescript((ROOT/"database"/"schema.sql").read_text(encoding="utf-8"))
    conn.commit(); conn.close()

def log(message):
    conn=db(); conn.execute("INSERT INTO activity_log(message) VALUES (?)",(message,)); conn.commit(); conn.close()

def rebuild_queue():
    global queue
    queue=QueueManager()
    conn=db()
    rows=conn.execute("""SELECT v.*, p.name FROM visits v JOIN patients p ON p.id=v.patient_id
       WHERE v.status='Waiting' AND (v.appointment_at IS NULL OR v.appointment_at<=?)
       ORDER BY v.sequence""",(datetime.now().isoformat(timespec="minutes"),)).fetchall()
    for v in rows:
        queue.add(v["id"],v["name"],v["token"],v["category"],v["sequence"],v["appointment_at"],True)
    conn.close()

def stats():
    conn=db(); today=date.today().isoformat()
    waiting=conn.execute("SELECT COUNT(*) FROM visits WHERE status='Waiting' AND date(created_at)=?",(today,)).fetchone()[0]
    in_consult=conn.execute("SELECT COUNT(*) FROM visits WHERE status='In consultation'").fetchone()[0]
    completed=conn.execute("SELECT COUNT(*) FROM visits WHERE status='Completed' AND date(completed_at)=?",(today,)).fetchone()[0]
    emergency=conn.execute("SELECT COUNT(*) FROM visits WHERE status='Waiting' AND category='Acute / Emergency'").fetchone()[0]
    appointments=conn.execute("SELECT COUNT(*) FROM appointments WHERE date(appointment_at)=? AND status NOT IN ('Cancelled','Completed')",(today,)).fetchone()[0]
    conn.close()
    return dict(waiting=waiting,in_consult=in_consult,completed=completed,emergency=emergency,appointments=appointments)

@app.context_processor
def common():
    return {"categories": CATEGORIES, "today": date.today().strftime("%A, %d %B %Y"), "active_endpoint": request.endpoint}

@app.route("/")
def dashboard():
    rebuild_queue(); conn=db()
    nextrow=conn.execute("""SELECT v.*,p.name,p.age FROM visits v JOIN patients p ON p.id=v.patient_id
      WHERE v.status='Waiting' AND (v.appointment_at IS NULL OR v.appointment_at<=?) ORDER BY v.sequence""",(datetime.now().isoformat(timespec="minutes"),)).fetchall()
    # queue ordering from actual heap; map IDs to richer rows
    byid={r["id"]:r for r in nextrow}
    ordered=[byid[x[3]] for x in queue.ordered() if x[3] in byid]
    recent=conn.execute("SELECT message,created_at FROM activity_log ORDER BY id DESC LIMIT 6").fetchall()
    conn.close()
    return render_template("dashboard.html",stats=stats(),queue_rows=ordered[:5],next_patient=ordered[0] if ordered else None,recent=recent)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        f=request.form
        try: category=validate_category(f.get("category",""))
        except ValueError as e: flash(str(e),"error"); return redirect(url_for("register"))
        if not f.get("name","").strip() or not f.get("complaint","").strip():
            flash("Patient name and chief complaint are required.","error"); return redirect(url_for("register"))
        conn=db()
        try:
            conn.execute("BEGIN")
            pid="PD-"+uuid.uuid4().hex[:8].upper()
            cur=conn.execute("""INSERT INTO patients(patient_id,name,age,sex,phone,religion,location,occupation)
             VALUES(?,?,?,?,?,?,?,?)""",(pid,f["name"].strip(),f.get("age") or None,f.get("sex"),f.get("phone"),f.get("religion"),f.get("location"),f.get("occupation")))
            patient_pk=cur.lastrowid
            seq=conn.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM visits").fetchone()[0]
            token=f"T{seq:03d}-{date.today().strftime('%d%m')}"
            appointment=f.get("appointment_at") or None
            status="Waiting"
            conn.execute("""INSERT INTO visits(patient_id,token,complaint,complaint_duration,hpi,past_history,personal_history,menstrual_history,family_history,treatment_history,general_appearance,bp,pulse,temperature,respiratory_rate,spo2,exam_notes,clinician,category,visit_type,status,appointment_at,sequence)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(patient_pk,token,f["complaint"].strip(),f.get("complaint_duration"),f.get("hpi"),f.get("past_history"),f.get("personal_history"),f.get("menstrual_history"),f.get("family_history"),f.get("treatment_history"),f.get("general_appearance"),f.get("bp"),f.get("pulse"),f.get("temperature"),f.get("respiratory_rate"),f.get("spo2"),f.get("exam_notes"),f.get("clinician"),category,f.get("visit_type","Walk-in"),status,appointment,seq))
            visit_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            if appointment:
                conn.execute("INSERT INTO appointments(patient_id,visit_id,appointment_at,clinician,visit_type,status) VALUES(?,?,?,?,?,'Scheduled')",(patient_pk,visit_id,appointment,f.get("clinician"),f.get("visit_type","Scheduled appointment")))
            conn.execute("INSERT INTO activity_log(message) VALUES (?)",(f"Registered {f['name'].strip()} · {token}",))
            conn.commit()
        except Exception:
            conn.rollback(); conn.close(); raise
        conn.close(); rebuild_queue()
        flash(f"Registered successfully — Patient ID {pid}, token {token}.","success")
        return redirect(url_for("history",patient_id=patient_pk))
    return render_template("register_patient.html")

@app.route("/queue")
def live_queue():
    rebuild_queue(); conn=db()
    rows=conn.execute("""SELECT v.*,p.patient_id AS public_id,p.name,p.age FROM visits v JOIN patients p ON p.id=v.patient_id
      ORDER BY CASE v.status WHEN 'Waiting' THEN 0 WHEN 'In consultation' THEN 1 WHEN 'Completed' THEN 2 ELSE 3 END, v.sequence DESC""").fetchall()
    conn.close()
    flt=request.args.get("status","All")
    if flt!="All": rows=[r for r in rows if r["status"]==flt]
    return render_template("live_queue.html",rows=rows,filter_status=flt)

@app.post("/visit/<int:visit_id>/action")
def visit_action(visit_id):
    action=request.form.get("action")
    conn=db(); row=conn.execute("SELECT v.*,p.name FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.id=?",(visit_id,)).fetchone()
    if not row: conn.close(); flash("Visit not found.","error"); return redirect(url_for("live_queue"))
    if action=="call" and row["status"]=="Waiting": status="In consultation"
    elif action=="complete" and row["status"]=="In consultation": status="Completed"
    elif action=="cancel" and row["status"]=="Waiting": status="Cancelled"
    else: conn.close(); flash("That action is not valid for the current visit status.","error"); return redirect(url_for("live_queue"))
    conn.execute("UPDATE visits SET status=?, completed_at=CASE WHEN ?='Completed' THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE id=?",(status,status,visit_id))
    conn.execute("INSERT INTO activity_log(message) VALUES (?)",(f"{row['name']} · {status}",))
    conn.commit(); conn.close(); rebuild_queue(); flash(f"Visit marked {status.lower()}.","success")
    return redirect(request.referrer or url_for("live_queue"))

@app.post("/call-next")
def call_next():
    rebuild_queue(); item=queue.peek()
    if not item: flash("No eligible checked-in patients are waiting.","error"); return redirect(url_for("live_queue"))
    return redirect(url_for("visit_action",visit_id=item[3])) if False else _call_visit(item[3])

def _call_visit(visit_id):
    conn=db(); conn.execute("UPDATE visits SET status='In consultation' WHERE id=? AND status='Waiting'",(visit_id,))
    row=conn.execute("SELECT p.name FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.id=?",(visit_id,)).fetchone()
    if row: conn.execute("INSERT INTO activity_log(message) VALUES (?)",(f"Called next patient: {row['name']}",))
    conn.commit(); conn.close(); rebuild_queue(); flash("Next eligible patient called.","success"); return redirect(url_for("live_queue"))

@app.route("/search", methods=["GET","POST"])
def search():
    q=request.values.get("q","").strip(); results=[]; recent=[]
    conn=db()
    if q:
        results=search_patients(conn,q)
        conn.execute("INSERT INTO search_history(query) VALUES (?)",(q,)); conn.commit()
    recent=conn.execute("SELECT query,searched_at FROM search_history ORDER BY id DESC LIMIT 8").fetchall()
    conn.close()
    return render_template("search_patient.html",q=q,results=results,recent=recent)

@app.post("/search/clear")
def clear_search():
    conn=db(); conn.execute("DELETE FROM search_history"); conn.commit(); conn.close(); return redirect(url_for("search"))

@app.route("/patient/<int:patient_id>")
def history(patient_id):
    conn=db(); patient=conn.execute("SELECT * FROM patients WHERE id=?",(patient_id,)).fetchone()
    if not patient: conn.close(); flash("Patient not found.","error"); return redirect(url_for("search"))
    visits=conn.execute("SELECT * FROM visits WHERE patient_id=? ORDER BY id DESC",(patient_id,)).fetchall()
    appts=conn.execute("SELECT * FROM appointments WHERE patient_id=? ORDER BY appointment_at DESC",(patient_id,)).fetchall()
    conn.close(); return render_template("patient_history.html",patient=patient,visits=visits,appointments=appts)

@app.route("/appointments", methods=["GET","POST"])
def appointments():
    conn=db()
    if request.method=="POST":
        f=request.form; patient=conn.execute("SELECT id FROM patients WHERE patient_id=? OR name=? COLLATE NOCASE",(f.get("patient_ref"),f.get("patient_ref"))).fetchone()
        if not patient: conn.close(); flash("Patient ID or exact patient name not found. Register the patient first.","error"); return redirect(url_for("appointments"))
        if not f.get("appointment_at"): conn.close(); flash("Choose an appointment date and time.","error"); return redirect(url_for("appointments"))
        conn.execute("INSERT INTO appointments(patient_id,appointment_at,clinician,visit_type,status,notes) VALUES(?,?,?,?,?,?)",(patient["id"],f["appointment_at"],f.get("clinician"),f.get("visit_type","Scheduled appointment"),"Scheduled",f.get("notes")))
        conn.commit(); flash("Appointment scheduled.","success")
    rows=conn.execute("SELECT a.*,p.name,p.patient_id AS public_id FROM appointments a JOIN patients p ON p.id=a.patient_id ORDER BY a.appointment_at DESC").fetchall()
    conn.close(); return render_template("appointments.html",rows=rows)

@app.post("/appointment/<int:appointment_id>/<action>")
def appointment_action(appointment_id,action):
    if action not in ("cancel","checkin","complete","missed"): flash("Invalid appointment action.","error")
    else:
        status={"cancel":"Cancelled","checkin":"Checked in","complete":"Completed","missed":"Missed"}[action]
        conn=db(); conn.execute("UPDATE appointments SET status=? WHERE id=?",(status,appointment_id)); conn.commit(); conn.close(); flash(f"Appointment marked {status.lower()}.","success")
    return redirect(url_for("appointments"))

@app.route("/reports")
def reports():
    conn=db()
    categories=conn.execute("SELECT category,COUNT(*) n FROM visits GROUP BY category ORDER BY n DESC").fetchall()
    statuses=conn.execute("SELECT status,COUNT(*) n FROM appointments GROUP BY status").fetchall()
    daily=conn.execute("SELECT date(created_at) day,COUNT(*) n FROM visits GROUP BY date(created_at) ORDER BY day DESC LIMIT 7").fetchall()
    avg=conn.execute("""SELECT AVG((julianday(COALESCE(completed_at,CURRENT_TIMESTAMP))-julianday(created_at))*1440) FROM visits WHERE status='Completed'""").fetchone()[0]
    conn.close()
    return render_template("reports.html",stats=stats(),categories=categories,statuses=statuses,daily=daily,avg=round(avg,1) if avg else None)

@app.route("/dsa")
def dsa(): return render_template("dsa_explanation.html")

@app.route("/api/queue")
def api_queue():
    rebuild_queue()
    return jsonify([{"visit_id":x[3],"name":x[4],"token":x[5],"category":x[6],"position":i+1} for i,x in enumerate(queue.ordered())])

if __name__=="__main__":
    init_db()
    rebuild_queue()
    app.run(debug=True)
