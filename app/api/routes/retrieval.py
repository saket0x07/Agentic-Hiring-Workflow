import json
from fastapi import APIRouter, HTTPException

from app.graph.retrieval_state import RetrievalState
from app.graph.retrieval_workflow import retrieval_workflow
from app.services.job_service import JobService

router = APIRouter(
    prefix="/retrieval",
    tags=["Resume Retrieval"]
)

job_service = JobService()


from typing import Optional
from pydantic import BaseModel


class RetrievalRequest(BaseModel):
    top_k: int = 5
    min_experience_years: Optional[float] = None
    required_degree: Optional[str] = None


@router.post("/{job_id}")
def retrieve_candidates(
    job_id: str,
    top_k: int = 5,
    min_experience_years: Optional[float] = None,
    required_degree: Optional[str] = None,
    request_body: Optional[RetrievalRequest] = None
):
    """
    Retrieve top matching candidates for a Job Description using Hard Pre-Filtering + Hybrid Search.
    """

    job = job_service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    # Resolve parameters from body or query params
    final_top_k = request_body.top_k if request_body and request_body.top_k != 5 else top_k
    final_min_exp = request_body.min_experience_years if request_body and request_body.min_experience_years is not None else min_experience_years
    final_req_deg = request_body.required_degree if request_body and request_body.required_degree else required_degree

    filters = {}
    if final_min_exp is not None:
        filters["min_experience_years"] = final_min_exp
    if final_req_deg is not None:
        filters["required_degree"] = final_req_deg

    jd_val = job.generated_jd
    job_description_str = json.dumps(jd_val) if isinstance(jd_val, dict) else str(jd_val)

    state = RetrievalState(
        job_id=job_id,
        job_description=job_description_str,
        top_k=final_top_k,
        filters=filters if filters else None
    )


    result = retrieval_workflow.invoke(state)

    candidate_profiles = result.get("candidate_profiles", []) if isinstance(result, dict) else getattr(result, "candidate_profiles", [])

    candidates_list = []
    for candidate in candidate_profiles:
        profile_data = candidate["profile"]
        if hasattr(profile_data, "model_dump"):
            profile_data = profile_data.model_dump()
        candidates_list.append({
            "resume_id": candidate["resume_id"],
            "similarity_score": round(candidate.get("similarity_score", 0.0) * 100, 2),
            "rrf_score": round(candidate.get("rrf_score", 0.0), 4),
            "bm25_score": round(candidate.get("bm25_score", 0.0), 2),
            "bm25_rank": candidate.get("bm25_rank", 0),
            "vector_rank": candidate.get("vector_rank", 0),
            "rerank_score": round(candidate.get("rerank_score", 0.0), 2),
            "matched_chunk_type": candidate.get("matched_chunk_type", ""),
            "matched_chunk_text": candidate.get("matched_chunk_text", ""),
            "match_justification": candidate.get("match_justification", {}),
            "profile": profile_data
        })


    return {
        "job_id": job_id,
        "search_type": "Hybrid (BM25 + FAISS Vector + RRF + Cross-Encoder)",
        "total_candidates": len(candidates_list),
        "candidates": candidates_list
    }