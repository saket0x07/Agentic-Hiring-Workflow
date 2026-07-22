
import sqlite3

from app.core.config import settings
from app.schemas.job import Job


class JobService:

    def __init__(self):
        self.db_path = settings.SQLITE_DB_PATH

    def get_job(self, job_id: str):

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM jobs
            WHERE job_id = ?
            """,
            (job_id,)
        )

        row = cursor.fetchone()

        conn.close()

        if row is None:
            return None

        return Job.model_validate(dict(row))