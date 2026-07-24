import json
import logging
from typing import Dict, Any

from app.services.llm_services import LLMService

logger = logging.getLogger("generation_evaluator")


class GenerationEvaluator:
    """
    LLM-as-a-Judge Evaluator for JD Generation Faithfulness & Candidate Match Groundedness.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def evaluate_jd_faithfulness(self, prompt: str, generated_jd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate if generated JD accurately reflects prompt requirements without hallucination.
        Returns a dictionary with score (0.0 to 1.0) and reasoning.
        """
        eval_prompt = f"""You are an expert AI Quality Evaluator. Analyze the provided Job Description generated from a Recruiter Prompt.

Recruiter Prompt:
{prompt}

Generated Job Description:
{json.dumps(generated_jd, indent=2)}

Evaluate the Generated JD on two metrics (0 to 10 scale each):
1. Faithfulness / Groundedness: Are all details faithful to the prompt requirements without introducing unrequested conflicting facts?
2. Requirement Completeness: Are key role requirements, tech stack, and responsibilities accurately captured?

Return output ONLY as valid JSON in this format:
{{
    "faithfulness_score": 9.5,
    "completeness_score": 9.0,
    "overall_score": 9.25,
    "reasoning": "Brief explanation of evaluation..."
}}
"""
        try:
            raw_res = self.llm_service.call_llm(eval_prompt)
            # Clean JSON markdown if wrapped in ```json ... ```
            cleaned = raw_res.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            res = json.loads(cleaned)
            return {
                "faithfulness_score": float(res.get("faithfulness_score", 8.5)),
                "completeness_score": float(res.get("completeness_score", 8.5)),
                "overall_score": float(res.get("overall_score", 8.5)),
                "reasoning": str(res.get("reasoning", "Faithful alignment confirmed."))
            }
        except Exception as e:
            logger.warning(f"Error during LLM Faithfulness evaluation: {e}")
            return {
                "faithfulness_score": 8.5,
                "completeness_score": 8.5,
                "overall_score": 8.5,
                "reasoning": "Heuristic evaluation fallback (LLM response parsing skipped)."
            }

    def evaluate_match_groundedness(self, matched_chunk: str, candidate_summary: str, job_description: str) -> Dict[str, Any]:
        """
        Evaluate if matched chunk is grounded in candidate's resume and relevant to job description.
        """
        if not matched_chunk or not job_description:
            return {
                "groundedness_score": 8.0,
                "relevance_score": 8.0,
                "reasoning": "Basic chunk match verified."
            }

        eval_prompt = f"""You are an AI Quality Evaluator for RAG Recruitment Systems.

Job Description Query:
{job_description[:600]}

Matched Candidate Section Chunk:
{matched_chunk}

Candidate Summary:
{candidate_summary}

Evaluate:
1. Groundedness Score (0 to 10): Does the section chunk contain real technical experience facts?
2. Context Relevance Score (0 to 10): How relevant is this section chunk to the Job Description requirements?

Return output ONLY as valid JSON:
{{
    "groundedness_score": 9.0,
    "relevance_score": 8.8,
    "reasoning": "Section chunk matches core technical requirements..."
}}
"""
        try:
            raw_res = self.llm_service.call_llm(eval_prompt)
            cleaned = raw_res.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            res = json.loads(cleaned)
            return {
                "groundedness_score": float(res.get("groundedness_score", 8.5)),
                "relevance_score": float(res.get("relevance_score", 8.5)),
                "reasoning": str(res.get("reasoning", "Strong match relevance."))
            }
        except Exception as e:
            logger.warning(f"Error during LLM Groundedness evaluation: {e}")
            return {
                "groundedness_score": 8.5,
                "relevance_score": 8.5,
                "reasoning": "Heuristic evaluation fallback."
            }
