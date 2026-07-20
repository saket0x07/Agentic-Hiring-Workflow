from typing import Optional

JD_GENERATION_SYSTEM_PROMPT = """You are a world-class Technical Recruitment Specialist and Job Description (JD) writer.

Your task is to analyze the hiring request provided by the recruiter and generate a comprehensive, professional, and engaging Job Description (JD).

STRICT OUTPUT FORMAT:
- job_title
- summary
- responsibilities
- must_have_skills
- nice_to_have_skills
- experience
- education
- interview_rounds

Return the output EXACTLY as a JSON object.
DO NOT include markdown formatting (```json), explanations, or any text outside the JSON.
Return Only Valid JSON.
"""

def build_jd_prompt(hiring_request: dict, feedback: Optional[str] = None) -> str:
    req_skills = hiring_request.get("required_skills") or []
    pref_skills = hiring_request.get("preferred_skills") or []

    prompt = f"""
    Generate a Job Description using the following Hiring Request.
    Role: {hiring_request.get("role", "")}
    Department: {hiring_request.get("department", "")}
    Experience: {hiring_request.get("experience", "")}
    Location: {hiring_request.get("location", "")}
    Employment Type: {hiring_request.get("employment_type", "")}
    Work Mode: {hiring_request.get("work_mode", "")}
    Budget: {hiring_request.get("budget", "N/A")}
    Required Skills: {', '.join(req_skills)}
    Preferred Skills: {', '.join(pref_skills)}
    Additional Notes: {hiring_request.get("notes", "N/A")}
    """

    if feedback:
        prompt += f"""
        RECRUITER REJECTION FEEDBACK & REVISION INSTRUCTIONS:
        "{feedback}"
        Please carefully adjust, revise, and improve the generated Job Description according to the feedback above.
        """

    return prompt