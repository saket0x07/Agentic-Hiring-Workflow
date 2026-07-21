import asyncio
import os
from pathlib import Path
import pytest
from app.services.database_service import DatabaseService
from app.services.pdf_service import PDFService
from app.agents.jd_generator import JDGenerationAgent

@pytest.mark.asyncio
async def test_hitl_flow():
    job_id = "TEST-HITL-999"
    hiring_request = {
        "role": "Senior AI Engineer",
        "department": "Engineering",
        "experience": "4 years",
        "location": "Remote",
        "employment_type": "full_time",
        "work_mode": "remote",
        "budget": "$150k",
        "required_skills": ["Python", "FastAPI", "LangGraph"],
        "preferred_skills": ["Docker", "Kubernetes"],
        "notes": "Must have LLM multi-agent experience"
    }

    db = DatabaseService()

    # 1. Initial Generation (Pending Approval)
    agent = JDGenerationAgent()
    initial_jd = await agent.generate(hiring_request)
    initial_jd_dict = initial_jd.model_dump()

    db.save_job(
        job_id=job_id,
        hiring_request=hiring_request,
        generated_jd=initial_jd_dict,
        status="PENDING_APPROVAL",
        approval_feedback=None,
        retry_count=0,
        pdf_path=None
    )

    job_step1 = db.get_job(job_id)
    assert job_step1["status"] == "PENDING_APPROVAL"
    assert job_step1["pdf_path"] is None
    assert job_step1["retry_count"] == 0
    print("Step 1 Passed: Initial JD saved with PENDING_APPROVAL and no PDF.")

    # 2. Rejection & Feedback Revision
    feedback = "Please emphasize experience with LangGraph multi-agent architectures."
    revised_jd = await agent.generate(hiring_request, feedback=feedback)
    revised_jd_dict = revised_jd.model_dump()

    db.update_rejection_and_jd(
        job_id=job_id,
        new_generated_jd=revised_jd_dict,
        feedback=feedback,
        new_retry_count=1
    )

    job_step2 = db.get_job(job_id)
    assert job_step2["status"] == "PENDING_APPROVAL"
    assert job_step2["retry_count"] == 1
    assert job_step2["approval_feedback"] == feedback
    assert job_step2["pdf_path"] is None
    print("Step 2 Passed: JD rejected and regenerated with feedback, retry_count=1, no PDF.")

    # 3. Approval & PDF Generation
    pdf_service = PDFService()
    pdf_path = await pdf_service.generate_job_description_pdf(job_id, job_step2["generated_jd"])

    db.update_approval_status(job_id=job_id, status="APPROVED", pdf_path=pdf_path)

    job_step3 = db.get_job(job_id)
    assert job_step3["status"] == "APPROVED"
    assert job_step3["pdf_path"] is not None
    assert Path(job_step3["pdf_path"]).exists()
    print(f"Step 3 Passed: JD approved, PDF generated at {job_step3['pdf_path']}.")

if __name__ == "__main__":
    asyncio.run(test_hitl_flow())
