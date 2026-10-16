from collections import OrderedDict
from threading import RLock

from app.models import WorkflowRecord


class WorkflowStore:
    """Thread-safe in-memory history, bounded to the newest records."""

    def __init__(self, max_records: int = 100):
        if max_records < 1:
            raise ValueError("max_records must be at least one.")
        self._records: OrderedDict[str, WorkflowRecord] = OrderedDict()
        self._lock = RLock()
        self.max_records = max_records

    def save(self, record: WorkflowRecord) -> None:
        with self._lock:
            self._records[record.workflow_id] = record.model_copy(deep=True)
            self._records.move_to_end(record.workflow_id)
            while len(self._records) > self.max_records:
                self._records.popitem(last=False)

    def get(self, workflow_id: str) -> WorkflowRecord | None:
        with self._lock:
            record = self._records.get(workflow_id)
            return record.model_copy(deep=True) if record else None

    def list_recent(self) -> list[WorkflowRecord]:
        with self._lock:
            return [record.model_copy(deep=True) for record in reversed(self._records.values())]
