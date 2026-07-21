import json
from json_repair import repair_json

from app.prompts.resume_parsing import RESUME_PARSING_SYSTEM_PROMPT, build_resume_parsing_prompt
from app.schemas.candidate_profile import CandidateProfile
from app.services.llm_services import LLMService


class ResumeParserAgent:
    """
    Parses raw resume text into a structured CandidateProfile.
    """

    def __init__(self):
        self.llm = LLMService()

    async def parse(self, resume_text: str) -> CandidateProfile:
        user_prompt = build_resume_parsing_prompt(resume_text)

        response = await self.llm.generate(
            system_prompt=RESUME_PARSING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        start_idx = response.find("{")
        end_idx = response.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_response = response[start_idx : end_idx + 1]
        else:
            clean_response = response.strip()

        try:
            parsed_json = json.loads(clean_response, strict=False)
        except Exception:
            repaired_str = repair_json(clean_response)
            parsed_json = json.loads(repaired_str, strict=False)

        parsed_json["raw_text"] = resume_text

        return CandidateProfile.model_validate(parsed_json)