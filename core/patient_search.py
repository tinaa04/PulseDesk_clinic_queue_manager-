def search_patients(conn, query):
    q = (query or "").strip()
    if not q:
        return []
    return conn.execute("""SELECT * FROM patients
        WHERE patient_id LIKE ? OR name LIKE ? OR phone LIKE ?
        ORDER BY name COLLATE NOCASE LIMIT 100""",
        (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
