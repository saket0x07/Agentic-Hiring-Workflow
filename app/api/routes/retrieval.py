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


@router.post("/{job_id}")
def retrieve_candidates(
    job_id: str,
    top_k: int = 5
):
    """
    Retrieve top matching candidates for a Job Description using Hybrid Search (BM25 + FAISS Vector + RRF + Reranker).
    """

    job = job_service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    jd_val = job.generated_jd
    job_description_str = json.dumps(jd_val) if isinstance(jd_val, dict) else str(jd_val)

    state = RetrievalState(
        job_id=job_id,
        job_description=job_description_str,
        top_k=top_k
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
            "profile": profile_data
        })

    return {
        "job_id": job_id,
        "search_type": "Hybrid (BM25 + FAISS Vector + RRF + Cross-Encoder)",
        "total_candidates": len(candidates_list),
        "candidates": candidates_list
    }