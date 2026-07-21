import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from app.graph.resume_state import ResumeState
from app.graph.resume_workflow import resume_workflow

router = APIRouter(prefix="/resumes", tags=["Resumes"])

UPLOAD_DIRECTORY = Path("data/resumes")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """UPLOAD, PARSE, STORE, EMBED, AND INDEX A RESUME VIA LANGGRAPH WORKFLOW"""
    extension = Path(file.filename).suffix.lower()
    if extension not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    resume_id = str(uuid.uuid4())
    saved_file = UPLOAD_DIRECTORY / f"{resume_id}{extension}"

    with saved_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        initial_state = ResumeState(
            resume_id=resume_id,
            file_path=saved_file,
        )
        final_state = await resume_workflow.ainvoke(initial_state)

        profile = final_state.get("candidate_profile")
        profile_data = profile.model_dump() if profile and hasattr(profile, "model_dump") else profile

        return {
            "message": "Resume uploaded and indexed successfully",
            "resume_id": resume_id,
            "status": final_state.get("status", "INDEXED"),
            "candidate_profile": profile_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))