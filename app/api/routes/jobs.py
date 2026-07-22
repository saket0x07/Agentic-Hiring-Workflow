import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.hiring_request import HiringRequest
from app.graph.workflow import graph
from app.services.database_service import DatabaseService
from app.services.pdf_service import PDFService
from app.agents.jd_generator import JDGenerationAgent
from app.core.logger import logger

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

class RejectRequest(BaseModel):
    feedback: str = Field(..., description="Recruiter feedback explaining rejection or needed revisions")

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_job(request: HiringRequest):
    """
    Generate initial Job Description and store in database with PENDING_APPROVAL status.
    No PDF is generated at this stage.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Received hiring request to create job_id: {job_id}")

    state = {
        "job_id": job_id,
        "workflow_stage": "START",
        "status": "PENDING",
        "hiring_request": request.model_dump(),
        "generated_jd": None,
        "pdf_path": None,
        "approved": False,
        "feedback": None,
        "messages": [],
        "errors": []
    }
    
    result = await graph.ainvoke(state)
    
    return {
        "message": "Job Description generated and awaiting approval.",
        "job_id": job_id,
        "status": result.get("status", "PENDING_APPROVAL"),
        "generated_jd": result.get("generated_jd"),
        "pdf_path": None
    }

@router.get("/")
async def list_all_jobs():
    """
    Get list of all Job Descriptions from database.
    """
    db = DatabaseService()
    return db.list_jobs()

@router.get("/{job_id}")
async def get_job(job_id: str):
    """
    Get Job Description details and status from database.
    """
    db = DatabaseService()
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job record '{job_id}' not found.")
    return job

@router.post("/{job_id}/approve")
async def approve_job(job_id: str):
    """
    Approve the Job Description:
    1. Update status to 'APPROVED'.
    2. Generate PDF via PDFService and save to output/job_descriptions/{job_id}.pdf.
    3. Save pdf_path into database.
    """
    logger.info(f"Approving job_id: {job_id}")
    db = DatabaseService()
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job record '{job_id}' not found.")

    if job["status"] == "APPROVED":
        return {
            "message": "Job description is already approved.",
            "job_id": job_id,
            "status": job["status"],
            "pdf_path": job["pdf_path"],
            "generated_jd": job["generated_jd"]
        }

    # Generate PDF only after explicit approval
    pdf_service = PDFService()
    pdf_path = await pdf_service.generate_job_description_pdf(job_id, job["generated_jd"])

    # Update SQLite database record
    updated_job = db.update_approval_status(
        job_id=job_id,
        status="APPROVED",
        pdf_path=pdf_path
    )

    return {
        "message": "Job Description successfully approved and PDF generated.",
        "job_id": job_id,
        "status": updated_job["status"],
        "pdf_path": updated_job["pdf_path"],
        "generated_jd": updated_job["generated_jd"]
    }

@router.post("/{job_id}/reject")
async def reject_job(job_id: str, payload: RejectRequest):
    """
    Reject the Job Description:
    1. Accept recruiter feedback.
    2. Increment retry_count.
    3. Regenerate JD using feedback via JDGenerationAgent.
    4. Update SQLite database record with new JD and status 'PENDING_APPROVAL'.
    5. Do NOT generate PDF.
    """
    logger.info(f"Rejecting job_id: {job_id} with feedback: '{payload.feedback}'")
    db = DatabaseService()
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job record '{job_id}' not found.")

    current_retry_count = job.get("retry_count", 0) + 1
    hiring_request = job["hiring_request"]

    # Regenerate JD incorporating recruiter feedback
    agent = JDGenerationAgent()
    new_generated_jd = await agent.generate(hiring_request, feedback=payload.feedback)
    new_jd_dict = new_generated_jd.model_dump()

    # Update SQLite record
    updated_job = db.update_rejection_and_jd(
        job_id=job_id,
        new_generated_jd=new_jd_dict,
        feedback=payload.feedback,
        new_retry_count=current_retry_count
    )

    return {
        "message": "Job Description rejected and regenerated based on feedback. Awaiting review.",
        "job_id": job_id,
        "status": updated_job["status"],
        "retry_count": updated_job["retry_count"],
        "approval_feedback": updated_job["approval_feedback"],
        "generated_jd": updated_job["generated_jd"],
        "pdf_path": None
    }
