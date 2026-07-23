from typing import Optional

JD_GENERATION_SYSTEM_PROMPT = """You are a world-class Technical Recruitment Specialist and Job Description (JD) writer.

Your task is to analyze the hiring request provided by the recruiter and generate a comprehensive, professional, and engaging Job Description (JD).

STRICT LAYOUT & CONCISENESS RULES:
1. SINGLE PAGE FIT: The generated content MUST be concise so that the formatted PDF fits cleanly on a SINGLE A4 PAGE.
   - Summary: Max 2-3 sentences.
   - Key Responsibilities: Max 4-5 bullet points.
   - Must-Have Skills: Max 5-6 core skills.
   - Nice-to-Have Skills: Max 3-4 skills.
   - Interview Process: Max 3-4 concise rounds.

2. CHARACTER ENCODING:
   - Use ONLY standard ASCII hyphens (-) for hyphenated words (e.g., 'real-time', 'cutting-edge', 'co-design').
   - DO NOT use special Unicode hyphens (\u2011), en-dashes (\u2013), em-dashes (\u2014), or soft hyphens.

STRICT OUTPUT FORMAT:
- job_title: string
- summary: string
- responsibilities: list of strings (JSON Array e.g. ["item 1", "item 2"])
- must_have_skills: list of strings (JSON Array e.g. ["skill 1", "skill 2"])
- nice_to_have_skills: list of strings (JSON Array e.g. ["skill 1", "skill 2"])
- experience: string
- education: string
- interview_rounds: list of strings (JSON Array e.g. ["round 1", "round 2"])

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