import json
from typing import Optional
from app.prompts.jd_generation import JD_GENERATION_SYSTEM_PROMPT, build_jd_prompt
from app.services.llm_services import LLMService
from app.schemas.job_description import JobDescription
from app.core.logger import logger

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

        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.strip("`")
            if clean_response.startswith("json"):
                clean_response = clean_response[4:].strip()

        data = json.loads(clean_response)
        
        # Mapping fallback if title was returned instead of job_title
        if "title" in data and "job_title" not in data:
            data["job_title"] = data["title"]

        jd = JobDescription.model_validate(data)
        return jd