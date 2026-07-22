from typing import Optional, Dict, Any
from app.services.database_service import DatabaseService


class JobRecord:
    def __init__(self, data: dict):
        self._data = data
        self.job_id = data.get("job_id")
        self.generated_jd = data.get("generated_jd")
        self.status = data.get("status")
        self.hiring_request = data.get("hiring_request")
        self.pdf_path = data.get("pdf_path")

    def __getitem__(self, item):
        return self._data[item]

    def get(self, item, default=None):
        return self._data.get(item, default)


class JobService:
    """
    Service wrapper for job database operations.
    """

    def __init__(self, db_service: Optional[DatabaseService] = None):
        self.db_service = db_service or DatabaseService()

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        data = self.db_service.get_job(job_id)
        if not data:
            return None
        return JobRecord(data)

    def list_jobs(self) -> list:
        return [JobRecord(data) for data in self.db_service.list_jobs()]
