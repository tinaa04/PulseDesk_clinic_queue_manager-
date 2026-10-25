import unittest, tempfile, sqlite3
from pathlib import Path
from core.patient_search import search_patients
class SearchTests(unittest.TestCase):
    def test_search(self):
        conn=sqlite3.connect(":memory:"); conn.row_factory=sqlite3.Row
        conn.execute("CREATE TABLE patients(patient_id TEXT,name TEXT,phone TEXT)")
        conn.execute("INSERT INTO patients VALUES('PD-123','Aanya Sharma','999')")
        self.assertEqual(len(search_patients(conn,"Aanya")),1)
        self.assertEqual(len(search_patients(conn,"PD-123")),1)
        self.assertEqual(len(search_patients(conn,"missing")),0)
if __name__=="__main__": unittest.main()
