import unittest
from core.queue_manager import QueueManager
class QueueTests(unittest.TestCase):
    def setUp(self): self.q=QueueManager()
    def test_priority_then_fifo(self):
        self.q.add(1,"A","T1","Minor / Routine",1)
        self.q.add(2,"B","T2","Minor / Routine",2)
        self.q.add(3,"C","T3","Acute / Emergency",3)
        self.assertEqual([x[3] for x in self.q.ordered()],[3,1,2])
    def test_update_priority(self):
        self.q.add(1,"A","T1","Minor / Routine",1)
        self.q.add(2,"B","T2","Chronic Illness",2)
        self.assertTrue(self.q.update_priority(1,"Acute / Emergency"))
        self.assertEqual(self.q.peek()[3],1)
    def test_cancel_and_pop(self):
        self.q.add(1,"A","T1","Minor / Routine",1)
        self.q.add(2,"B","T2","Chronic Illness",2)
        self.q.cancel(2)
        self.assertEqual(self.q.pop()[3],1)
        self.assertIsNone(self.q.pop())
    def test_position(self):
        self.q.add(1,"A","T1","Minor / Routine",1)
        self.q.add(2,"B","T2","Acute / Emergency",2)
        self.assertEqual(self.q.position(1),2)
if __name__=="__main__": unittest.main()
