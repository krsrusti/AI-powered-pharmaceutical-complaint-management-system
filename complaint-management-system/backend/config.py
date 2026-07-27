"""
Centralized app settings, loaded from environment variables (.env).

Groq model choice rationale:
  - GROQ_MODEL_FAST (gemma2-9b-it): used for extraction and completeness
    checks — high volume, latency-sensitive calls where a smaller model is
    sufficient since the task is closer to structured parsing than deep reasoning.
  - GROQ_MODEL_REASONING (llama-3.3-70b-versatile): used specifically for risk
    assessment, where the quality of reasoning (why a risk level was assigned)
    matters more than speed, and the task benefits from a larger model.

Database: PostgreSQL by default. SQLAlchemy + psycopg2 driver.

Embeddings: Groq has no embeddings endpoint, so duplicate detection uses a
local sentence-transformers model instead (no extra API key required).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Groq LLM ---
    GROQ_API_KEY: str = "your-groq-api-key-here"
    GROQ_MODEL_FAST: str = "gemma2-9b-it"
    GROQ_MODEL_REASONING: str = "llama-3.3-70b-versatile"
    GROQ_API_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MAX_RETRIES: int = 2
    LLM_TEMPERATURE: float = 0.2   # low temperature — extraction/risk logic should be consistent, not creative

    # --- Database (PostgreSQL) ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/complaint_db"

    # --- Duplicate detection ---
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.80

    # --- CORS / frontend ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- App ---
    APP_NAME: str = "Pharma Complaint Management System"
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()