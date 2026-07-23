from openai import AsyncOpenAI
from langsmith import traceable
from app.core.settings import settings

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
        self.model = settings.MODEL_NAME

    @traceable(name="LLM Generation", run_type="llm")
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""