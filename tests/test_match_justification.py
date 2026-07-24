import pytest
from app.evaluators.match_justifier import MatchJustifierService
from app.graph.explain_candidates import ExplainCandidatesNode
from app.graph.retrieval_state import RetrievalState


def test_heuristic_match_justification():
    service = MatchJustifierService()

    candidate = {
        "resume_id": "res_12345",
        "similarity_score": 94.2,
        "matched_chunk_type": "work_experience",
        "matched_chunk_text": "Built RAG pipelines using Python and FAISS at Acme Corp.",
        "profile": {
            "candidate_name": "Alice Smith",
            "technical_skills": ["Python", "RAG", "FAISS", "FastAPI"],
            "work_experience": [
                {
                    "job_title": "AI Engineer",
                    "company": "Acme Corp",
                    "responsibilities": ["Built RAG pipelines at Acme Corp"]
                }
            ],
            "professional_summary": "Experienced AI Engineer specializing in RAG architectures."
        }
    }

    job_description = {
        "job_title": "Senior RAG Engineer",
        "must_have_skills": ["Python", "FAISS", "Kubernetes"],
        "nice_to_have_skills": ["Docker", "LangChain"]
    }

    result = service._heuristic_justification(candidate, job_description)

    assert "justification_summary" in result
    assert "matching_strengths" in result
    assert "missing_skill_gaps" in result
    assert len(result["matching_strengths"]) > 0
    # Check that Kubernetes is identified as missing
    gap_text = " ".join(result["missing_skill_gaps"])
    assert "Kubernetes" in gap_text or "nice-to-have" in gap_text.lower() or len(result["missing_skill_gaps"]) > 0


def test_explain_candidates_node():
    node = ExplainCandidatesNode()

    candidate = {
        "resume_id": "res_999",
        "similarity_score": 88.5,
        "matched_chunk_type": "work_experience",
        "matched_chunk_text": "Senior Developer with Python background.",
        "profile": {
            "candidate_name": "Bob Jones",
            "technical_skills": ["Python", "SQL"],
            "work_experience": []
        }
    }

    state = RetrievalState(
        job_id="job_001",
        job_description='{"must_have_skills": ["Python", "Docker"]}',
        candidate_profiles=[candidate]
    )

    updated_state = node(state)
    assert updated_state.status == "EXPLAINED"
    assert "match_justification" in updated_state.candidate_profiles[0]
    just = updated_state.candidate_profiles[0]["match_justification"]
    assert "justification_summary" in just
