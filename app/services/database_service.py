import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.logger import logger
from app.core.settings import settings

class DatabaseService:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_file = Path(db_path)
        else:
            # Extract file path from sqlite:///./database/hiring.db
            url = settings.DATABASE_URL
            clean_path = url.replace("sqlite:///", "")
            self.db_file = Path(clean_path)

        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize job_descriptions table in SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    job_id TEXT PRIMARY KEY,
                    hiring_request TEXT NOT NULL,
                    generated_jd TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
                    approval_feedback TEXT,
                    retry_count INTEGER DEFAULT 0,
                    pdf_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_job(self, job_id: str, hiring_request: Dict[str, Any], generated_jd: Dict[str, Any], status: str = "PENDING_APPROVAL", approval_feedback: Optional[str] = None, retry_count: int = 0, pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """Save a new job record to SQLite."""
        now = datetime.now().isoformat()
        hr_json = json.dumps(hiring_request)
        jd_json = json.dumps(generated_jd)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO job_descriptions (
                    job_id, hiring_request, generated_jd, status, approval_feedback, retry_count, pdf_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, hr_json, jd_json, status, approval_feedback, retry_count, pdf_path, now, now))
            conn.commit()

        logger.info(f"Job record {job_id} saved to SQLite with status='{status}'.")
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job record by job_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_descriptions WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            job_dict = dict(row)
            job_dict["hiring_request"] = json.loads(job_dict["hiring_request"])
            job_dict["generated_jd"] = json.loads(job_dict["generated_jd"])
            return job_dict

    def update_approval_status(self, job_id: str, status: str, pdf_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update approval status and pdf_path for a job."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if pdf_path:
                cursor.execute("""
                    UPDATE job_descriptions
                    SET status = ?, pdf_path = ?, updated_at = ?
                    WHERE job_id = ?
                """, (status, pdf_path, now, job_id))
            else:
                cursor.execute("""
                    UPDATE job_descriptions
                    SET status = ?, updated_at = ?
                    WHERE job_id = ?
                """, (status, now, job_id))
            conn.commit()

        logger.info(f"Job {job_id} updated: status='{status}', pdf_path='{pdf_path}'.")
        return self.get_job(job_id)

    def update_rejection_and_jd(self, job_id: str, new_generated_jd: Dict[str, Any], feedback: str, new_retry_count: int) -> Optional[Dict[str, Any]]:
        """Update job record after rejection with new JD and incremented retry_count."""
        now = datetime.now().isoformat()
        jd_json = json.dumps(new_generated_jd)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE job_descriptions
                SET generated_jd = ?,
                    status = 'PENDING_APPROVAL',
                    approval_feedback = ?,
                    retry_count = ?,
                    pdf_path = NULL,
                    updated_at = ?
                WHERE job_id = ?
            """, (jd_json, feedback, new_retry_count, now, job_id))
            conn.commit()

        logger.info(f"Job {job_id} re-generated and updated after rejection (retry_count={new_retry_count}).")
        return self.get_job(job_id)
