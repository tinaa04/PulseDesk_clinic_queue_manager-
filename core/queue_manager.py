"""Real binary min-heap queue with FIFO tie-breaking."""
import heapq
from datetime import datetime

PRIORITY = {"Acute / Emergency": 0, "Chronic Illness": 1, "Follow-up / Scheduled": 2, "Minor / Routine": 3}

class QueueManager:
    def __init__(self):
        self.heap = []
        self.entries = {}

    def add(self, visit_id, patient_name, token, category, sequence, appointment_time=None, checked_in=True):
        if visit_id in self.entries:
            self.cancel(visit_id)
        if not checked_in:
            return
        rank = PRIORITY.get(category, 3)
        # Due appointments get a small scheduling advantage within their category.
        appt = 0
        if appointment_time:
            try:
                dt = datetime.fromisoformat(appointment_time)
                appt = 0 if dt <= datetime.now() else 1
            except ValueError:
                appt = 1
        item = [rank, appt, int(sequence), int(visit_id), patient_name, token, category]
        self.entries[int(visit_id)] = item
        heapq.heappush(self.heap, item)

    def cancel(self, visit_id):
        self.entries.pop(int(visit_id), None)

    def _valid(self):
        while self.heap and self.heap[0][3] not in self.entries:
            heapq.heappop(self.heap)

    def peek(self):
        self._valid()
        return self.heap[0] if self.heap else None

    def pop(self):
        item = self.peek()
        if item:
            heapq.heappop(self.heap)
            self.entries.pop(item[3], None)
        return item

    def update_priority(self, visit_id, category):
        item = self.entries.get(int(visit_id))
        if not item:
            return False
        item[0] = PRIORITY.get(category, 3)
        item[6] = category
        heapq.heapify(self.heap)
        return True

    def ordered(self):
        return sorted(self.entries.values(), key=lambda x: (x[0], x[1], x[2]))

    def position(self, visit_id):
        for i, item in enumerate(self.ordered(), 1):
            if item[3] == int(visit_id):
                return i
        return None
