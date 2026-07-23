import os
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)

class Settings(BaseSettings):
    """APPLICATION SETTINGS"""

    APP_NAME: str = "Agentic Hiring Workflow"
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # LLM providers
    OPENROUTER_API_KEY: str 
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL_NAME: str 
    
    # Langsmith
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "Hiring_Automation"

    # Database
    DATABASE_URL: str = "sqlite:///./database/hiring.db"

    VECTOR_DB: str = "faiss"
    FAISS_INDEX_PATH: str = "./data/vector_store"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    st = Settings()
    os.environ["LANGCHAIN_TRACING_V2"] = str(st.LANGCHAIN_TRACING_V2).lower()
    if st.LANGCHAIN_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = st.LANGCHAIN_ENDPOINT
    if st.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = st.LANGCHAIN_API_KEY
    if st.LANGCHAIN_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = st.LANGCHAIN_PROJECT
    return st

settings = get_settings()