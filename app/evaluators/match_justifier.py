import json
import logging
from typing import Dict, Any, List, Optional
import asyncio

from app.services.llm_services import LLMService

logger = logging.getLogger("match_justifier")


class MatchJustifierService:
    """
    Evaluator & Justification Engine for Candidate Match Rationale & Skill Gap Analysis.
    Generates actionable match insights, positive strengths, and missing skill gaps relative to the Job Description.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def generate_justification(
        self,
        candidate: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entrypoint to generate candidate match justification.
        Tries LLM-assisted semantic analysis first, with automatic heuristic fallback.
        """
        try:
            # Check if event loop is already running
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # If running inside active async loop, use heuristic directly or task-based call
                return self._heuristic_justification(candidate, job_description)
            else:
                return asyncio.run(self._async_generate_justification(candidate, job_description))
        except Exception as e:
            logger.warning(f"Failed to generate LLM match justification: {e}. Falling back to heuristic generator.")
            return self._heuristic_justification(candidate, job_description)

    async def _async_generate_justification(
        self,
        candidate: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        profile = candidate.get("profile") or candidate
        matched_chunk_text = candidate.get("matched_chunk_text", "")
        matched_chunk_type = candidate.get("matched_chunk_type", "")
        sim_score = candidate.get("similarity_score") or candidate.get("score") or 0.0

        # Build prompt inputs
        jd_str = json.dumps(job_description, indent=2) if isinstance(job_description, dict) else str(job_description)
        cand_str = json.dumps(profile, indent=2) if isinstance(profile, dict) else str(profile)

        system_prompt = (
            "You are an expert Executive Technical Recruiter and Candidate Match Evaluator. "
            "Analyze the candidate's parsed profile and top matching section chunk against the Job Description. "
            "Provide high-impact, concise match rationale, candidate strengths, and specific missing skill gaps."
        )

        user_prompt = f"""
Job Description:
{jd_str[:1500]}

Candidate Top Matched Section ({matched_chunk_type}):
{matched_chunk_text[:1000]}

Candidate Full Profile Summary:
{cand_str[:1500]}

Calculated Vector Similarity Score: {sim_score}%

Tasks:
1. Provide a 1-sentence "justification_summary" highlighting why this candidate matched (e.g., "Matched 94% on Work Experience: Built RAG pipelines at Acme Corp").
2. Identify 2 to 4 key "matching_strengths" (e.g., ["Built RAG pipelines at Acme Corp", "7+ years Python & LLM experience"]).
3. Identify 1 to 3 "missing_skill_gaps" explicitly required or nice-to-have in the JD that are absent or weak in candidate profile (e.g., ["Lacks Kubernetes experience required in JD"]).

Return output ONLY as valid JSON:
{{
    "justification_summary": "Matched X% on...",
    "matching_strengths": ["Strength 1", "Strength 2"],
    "missing_skill_gaps": ["Gap 1", "Gap 2"]
}}
"""
        try:
            raw_res = await self.llm_service.generate(system_prompt, user_prompt)
            cleaned = raw_res.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(cleaned)

            summary = data.get("justification_summary")
            strengths = data.get("matching_strengths", [])
            gaps = data.get("missing_skill_gaps", [])

            if summary and isinstance(strengths, list) and isinstance(gaps, list):
                return {
                    "justification_summary": str(summary),
                    "matching_strengths": [str(s) for s in strengths],
                    "missing_skill_gaps": [str(g) for g in gaps]
                }
        except Exception as e:
            logger.warning(f"Error parsing LLM match response: {e}")

        return self._heuristic_justification(candidate, job_description)

    def _heuristic_justification(
        self,
        candidate: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fast, reliable rule-based fallback match justification.
        Compares candidate technical skills and experience against JD requirements.
        """
        profile = candidate.get("profile") or candidate
        matched_chunk_text = candidate.get("matched_chunk_text", "")
        matched_chunk_type = candidate.get("matched_chunk_type", "")

        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        cand_skills = get_val(profile, "technical_skills") or []
        if not isinstance(cand_skills, list):
            cand_skills = [str(cand_skills)]
        cand_skills_lower = set(s.lower() for s in cand_skills if s)

        # Extract JD skills
        jd_must_skills = []
        jd_nice_skills = []
        if isinstance(job_description, dict):
            gen_jd = job_description.get("generated_jd") or job_description
            if isinstance(gen_jd, dict):
                jd_must_skills = gen_jd.get("must_have_skills") or []
                jd_nice_skills = gen_jd.get("nice_to_have_skills") or []
            else:
                jd_must_skills = job_description.get("must_have_skills") or []
        
        if not isinstance(jd_must_skills, list):
            jd_must_skills = [str(jd_must_skills)]
        if not isinstance(jd_nice_skills, list):
            jd_nice_skills = [str(jd_nice_skills)]

        all_jd_reqs = jd_must_skills + jd_nice_skills
        if not all_jd_reqs:
            all_jd_reqs = ["Python", "Machine Learning", "FastAPI", "Docker", "Kubernetes", "SQL", "Cloud"]

        # Calculate Matched Strengths
        matched_skills = []
        for sk in cand_skills:
            if any(req.lower() in sk.lower() or sk.lower() in req.lower() for req in all_jd_reqs):
                matched_skills.append(sk)

        # Extract Work Experience Context
        exps = get_val(profile, "work_experience") or []
        top_exp_str = ""
        if isinstance(exps, list) and exps:
            first_exp = exps[0]
            title = get_val(first_exp, "job_title") or get_val(first_exp, "designation") or "Developer"
            comp = get_val(first_exp, "company") or "Previous Employer"
            top_exp_str = f"{title} at {comp}"

        # Match justification summary logic
        section_label = str(matched_chunk_type).replace("_", " ").title() if matched_chunk_type else "Work Experience"
        if top_exp_str:
            just_summary = f"Matched on {section_label}: {top_exp_str}"
        elif matched_skills:
            just_summary = f"Matched on Technical Skills ({', '.join(matched_skills[:2])})"
        else:
            just_summary = f"Matched relevant candidate section ({section_label})"

        strengths = []
        if top_exp_str:
            strengths.append(f"Demonstrated background as {top_exp_str}")
        if matched_skills:
            strengths.append(f"Strong overlap in core skills: {', '.join(matched_skills[:4])}")
        elif cand_skills:
            strengths.append(f"Relevant technical skillset: {', '.join(cand_skills[:4])}")
        
        if matched_chunk_text:
            first_sentence = matched_chunk_text.strip().split("\n")[0][:100]
            strengths.append(f"Section Highlight: \"{first_sentence}...\"")

        # Calculate Missing Skill Gaps
        missing_gaps = []
        for req in jd_must_skills:
            if not any(req.lower() in sk.lower() or sk.lower() in req.lower() for sk in cand_skills_lower):
                # Also check full text
                summary = str(get_val(profile, "professional_summary") or "").lower()
                raw = str(get_val(profile, "raw_text") or "").lower()
                if req.lower() not in summary and req.lower() not in raw:
                    missing_gaps.append(f"Lacks {req} experience required in JD")

        if not missing_gaps and jd_nice_skills:
            for req in jd_nice_skills:
                if not any(req.lower() in sk.lower() for sk in cand_skills_lower):
                    missing_gaps.append(f"Nice-to-have skill not found: {req}")

        if not missing_gaps:
            missing_gaps.append("No critical skill gaps identified against JD requirements.")

        return {
            "justification_summary": just_summary,
            "matching_strengths": strengths[:3],
            "missing_skill_gaps": missing_gaps[:3]
        }
