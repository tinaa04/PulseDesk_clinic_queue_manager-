PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS patients (
 id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT UNIQUE NOT NULL,
 name TEXT NOT NULL, age INTEGER, sex TEXT, phone TEXT, religion TEXT,
 location TEXT, occupation TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS visits (
 id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL REFERENCES patients(id),
 token TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 complaint TEXT NOT NULL, complaint_duration TEXT, hpi TEXT, past_history TEXT,
 personal_history TEXT, menstrual_history TEXT, family_history TEXT, treatment_history TEXT,
 general_appearance TEXT, bp TEXT, pulse TEXT, temperature TEXT, respiratory_rate TEXT,
 spo2 TEXT, exam_notes TEXT, clinician TEXT, category TEXT NOT NULL,
 visit_type TEXT NOT NULL DEFAULT 'Walk-in', status TEXT NOT NULL DEFAULT 'Waiting',
 appointment_at TEXT, sequence INTEGER NOT NULL, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS appointments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL REFERENCES patients(id),
 visit_id INTEGER REFERENCES visits(id), appointment_at TEXT NOT NULL, clinician TEXT,
 visit_type TEXT NOT NULL DEFAULT 'Scheduled appointment', status TEXT NOT NULL DEFAULT 'Scheduled',
 notes TEXT
);
CREATE TABLE IF NOT EXISTS search_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT NOT NULL, searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS activity_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
