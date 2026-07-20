from app.agents.jd_generator import JDGenerationAgent
from app.graph.state import HiringState
from app.core.logger import logger
from app.services.database_service import DatabaseService

agent = JDGenerationAgent()

async def jd_generator_node(state: HiringState) -> HiringState:
    """Async node for generating JD and saving to SQLite with PENDING_APPROVAL status."""
    logger.info("Executing jd_generator_node...")

    hiring_request = state["hiring_request"]
    generated_jd = await agent.generate(hiring_request)
    
    job_id = state.get("job_id", "JOB-DEFAULT")
    jd_dict = generated_jd.model_dump()

    # Save to SQLite database (without generating a PDF)
    db = DatabaseService()
    db.save_job(
        job_id=job_id,
        hiring_request=hiring_request,
        generated_jd=jd_dict,
        status="PENDING_APPROVAL",
        approval_feedback=None,
        retry_count=0,
        pdf_path=None
    )

    state["generated_jd"] = jd_dict
    state["pdf_path"] = None
    state["workflow_stage"] = "PENDING_APPROVAL"
    state["status"] = "PENDING_APPROVAL"
    state["messages"].append("JD generated successfully and stored with PENDING_APPROVAL status.")
    return state