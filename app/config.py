from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    admin_token: str = ""
    embedding_model: str = "intfloat/multilingual-e5-base"
    embedding_revision: str = "main"
    embedding_device: str = "cpu"
    retrieval_k: int = Field(default=8, ge=1, le=20)
    candidate_k: int = Field(default=24, ge=1, le=100)
    chunk_tokens: int = Field(default=400, ge=80, le=450)
    chunk_overlap: int = Field(default=50, ge=0, le=70)
    gemini_timeout_seconds: int = Field(default=60, ge=5, le=180)
    data_dir: Path = ROOT / "data"
    @property
    def processed(self): return self.data_dir / "processed"
    @property
    def indexes(self): return self.data_dir / "indexes"

@lru_cache
def settings(): return Settings()
