from app.services.resume_extractor import ResumeExtractor
import shutil
import uuid
from pathlib import Path


from fastapi import APIRouter, File, HTTPException, UploadFile
from app.agents.resume_parser import ResumeParserAgent
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])

UPLOAD_DIRECTORY = Path("data/resumes")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

resume_service = ResumeService()
resume_parser = ResumeParserAgent()

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...)):
    """UPLOAD AND PARSE A RESUME """
    extension = Path(file.filename).suffix.lower()
    if extension not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    resume_id = str(uuid.uuid4())
    saved_file = UPLOAD_DIRECTORY / f"{resume_id}{extension}"

    with saved_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        raw_text = ResumeExtractor.extract_text(saved_file)
        candidate_profile = await resume_parser.parse(raw_text)

        resume_service.save_resume(resume_id=resume_id, profile=candidate_profile, file_path=str(saved_file))
        
        return {
            "message": "Resume uploaded successfully",
            "resume_id": resume_id,
            "candidate_profile": candidate_profile.model_dump()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    