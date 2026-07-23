import json
from typing import Optional

from json_repair import repair_json

from app.core.logger import logger
from app.prompts.jd_generation import JD_GENERATION_SYSTEM_PROMPT, build_jd_prompt
from app.schemas.job_description import JobDescription
from app.services.llm_services import LLMService


class JDGenerationAgent:
    def __init__(self):
        self.llm = LLMService()

    async def generate(self, hiring_request: dict, feedback: Optional[str] = None) -> JobDescription:
        """
        Generate or revise Job Description using LLM service asynchronously.
        """
        logger.info("JDGenerationAgent building prompt and calling LLM...")
        user_prompt = build_jd_prompt(hiring_request, feedback=feedback)

        response = await self.llm.generate(
            system_prompt=JD_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        start_idx = response.find("{")
        end_idx = response.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_response = response[start_idx : end_idx + 1]
        else:
            clean_response = response.strip()

        try:
            data = json.loads(clean_response, strict=False)
        except Exception:
            repaired_str = repair_json(clean_response)
            data = json.loads(repaired_str, strict=False)

        # Ensure list fields are lists of strings if LLM returns a single string
        for list_field in ["responsibilities", "must_have_skills", "nice_to_have_skills", "interview_rounds"]:
            val = data.get(list_field)
            if isinstance(val, str):
                parsed_items = [line.lstrip("-*• 1234567890.").strip() for line in val.splitlines() if line.strip()]
                data[list_field] = parsed_items if parsed_items else [val.strip()]

        jd = JobDescription.model_validate(data)
        return jd