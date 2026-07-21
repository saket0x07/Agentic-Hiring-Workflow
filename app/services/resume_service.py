import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Union

from app.schemas.candidate_profile import CandidateProfile


class ResumeService:
    """
    Handles all Resume database operations.
    """

    def __init__(self, db_path: str = "database/hiring.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS resumes(
            resume_id TEXT PRIMARY KEY,
            candidate_name TEXT,
            email TEXT,
            phone TEXT,
            candidate_profile TEXT,
            raw_text TEXT,
            file_path TEXT,
            uploaded_at TEXT
        )
        """
        )
        conn.commit()
        conn.close()

    def save_resume(
        self, resume_id: str, profile: Union[CandidateProfile, dict], file_path: str
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        if isinstance(profile, dict):
            candidate_name = profile.get("candidate_name")
            contact = profile.get("contact") or {}
            email = contact.get("email") if isinstance(contact, dict) else None
            phone = str(contact.get("phone")) if isinstance(contact, dict) and contact.get("phone") else None
            raw_text = profile.get("raw_text", "")
            profile_json = json.dumps(profile, default=str)
        else:
            candidate_name = profile.candidate_name
            email = profile.contact.email if profile.contact else None
            phone = str(profile.contact.phone) if (profile.contact and profile.contact.phone) else None
            raw_text = profile.raw_text
            profile_json = json.dumps(profile.model_dump(), default=str)

        cursor.execute(
            """
        INSERT OR REPLACE INTO resumes(resume_id, candidate_name, email, phone, candidate_profile, raw_text, file_path, uploaded_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)  
        """,
            (
                resume_id,
                candidate_name,
                email,
                phone,
                profile_json,
                raw_text,
                file_path,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def get_resume(self, resume_id: str):
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE resume_id=?", (resume_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_resumes(self):
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_resume(self, resume_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE resume_id=?", (resume_id,))
        conn.commit()
        conn.close()