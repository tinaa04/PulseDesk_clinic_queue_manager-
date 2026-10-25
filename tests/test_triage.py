import unittest
from core.triage import validate_category
class TriageTests(unittest.TestCase):
    def test_valid(self): self.assertEqual(validate_category("Acute / Emergency"),"Acute / Emergency")
    def test_invalid(self):
        with self.assertRaises(ValueError): validate_category("diagnose")
if __name__=="__main__": unittest.main()
