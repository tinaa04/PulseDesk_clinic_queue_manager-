# PulseDesk — Smart Clinic Queue Manager
**Tagline:** Organized Care. Happier Visits. 

PulseDesk is a clinic queue and patient management system built with Python, Flask, and SQLite. It helps organize patient visits, manage waiting queues, handle appointments, and access patient records through a simple web interface. The project demonstrates the practical application of Data Structures and Algorithms in clinic workflow management.

## Requirements
- Windows 10/11
- Python 3.10 or newer
- VS Code (recommended)

## Run on Windows
Open this folder in VS Code. In Terminal → New Terminal, run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use Command Prompt terminal:
```bat
.venv\Scripts\activate.bat
```
Then install requirements and run `python app.py`.

Open **http://127.0.0.1:5000** in your browser. SQLite database `database/pulsedesk.db` is initialized automatically when `app.py` starts. Stop with Ctrl+C.

## Pages
- **Dashboard:** real database-derived counts, next eligible patient, activity.
- **Register Patient:** demographic data, complaint and duration, visit category, visit type, clinician, appointment time, visit-specific history and examination fields.
- **Live Queue:** visit tokens, status actions, status filters, polling refresh.
- **Appointments:** schedule appointments and track status.
- **Search Patient:** search by patient ID, name, or phone; persistent search history.
- **Patient History:** patient profile, visit timeline, previous history/examination, appointment records.
- **Reports & Analytics:** category/status breakdown, daily registrations, estimated registration-to-completion time.
- **DSA Explanation:** describes the implemented data structures and scheduling policy.

## DSA notes
`core/queue_manager.py` uses Python `heapq` as a binary min-heap. Its composite key is `(category priority, appointment due flag, registration sequence, visit id, ...)`; lower category rank is earlier, due appointments sort before future ones within a category, and sequence provides FIFO tie-breaking. Acute/emergency has rank 0, chronic 1, follow-up/scheduled 2, minor/routine 3. These are staff-assigned scheduling categories only.
- Insert: O(log n)
- Peek: O(1)
- Pop: O(log n)
- Ordered display: O(n log n)
- Priority update uses `heapify`, O(n)
- Python dictionary active-entry lookup: average O(1)
- Patient search uses SQLite `LIKE` and can be O(n) without indexes.

The active queue is rebuilt from SQLite waiting visits, so the database—not browser memory—is authoritative. Future appointments are not queue-eligible until their appointment time. Appointment scheduling and a visit's triage category are separate concepts.

## Tests
```powershell
python -m unittest discover -s tests -v
```

## Notes and limitations
- This is a college demonstration, not a certified EHR or medical triage tool.
- The interface is intended for local demonstration. It does not implement login/role-based access control, production security hardening, backups, or multi-clinic support.
- The appointment page records appointment statuses; it is a starter workflow and does not yet create a new visit automatically when an appointment is checked in.
- Staff must decide triage and override priorities clinically. Real emergencies must follow the clinic's emergency protocol and must never be delayed by software.
- Avoid entering real patient information in a classroom/demo deployment.
