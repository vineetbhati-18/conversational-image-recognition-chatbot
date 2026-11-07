from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import torch


class Settings(BaseSettings):
    """
    Application Settings configured via environment variables or default fallbacks.
    Supports production cloud deployments (Render, Vercel, Supabase, Neon).
    """
    APP_NAME: str = "BEL Conversational Image Recognition Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Server Bindings
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, validation_alias="PORT")

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database Settings
    DATABASE_URL_ENV: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "bhati"
    DB_PASSWORD: str = ""
    DB_NAME: str = "bel_chatbot_db"

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_ENV:
            url = self.DATABASE_URL_ENV
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        if self.DB_PASSWORD:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql+asyncpg://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL_ENV:
            url = self.DATABASE_URL_ENV
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        if self.DB_PASSWORD:
            return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql+psycopg2://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # AI / ML Inference Configuration
    DEVICE_OVERRIDE: str = ""
    YOLO_MODEL_NAME: str = "yolov8n.pt"
    VQA_MODEL_NAME: str = "Salesforce/blip-vqa-base"
    HF_TOKEN: Optional[str] = Field(default=None, validation_alias="HF_TOKEN")
    CONFIDENCE_THRESHOLD: float = 0.35
    MAX_UPLOAD_SIZE_MB: int = 15

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR_ENV: Optional[str] = Field(default=None, validation_alias="UPLOAD_DIR")

    @property
    def UPLOAD_DIR(self) -> Path:
        if self.UPLOAD_DIR_ENV:
            p = Path(self.UPLOAD_DIR_ENV)
            p.mkdir(parents=True, exist_ok=True)
            return p
        default_dir = Path(__file__).resolve().parent.parent / "uploads"
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir

    @property
    def INFERENCE_DEVICE(self) -> str:
        """
        Determines the optimal PyTorch compute device:
        - Prefers Apple Silicon MPS if on macOS with Apple GPU
        - CUDA if available
        - Defaults to CPU
        """
        if self.DEVICE_OVERRIDE:
            return self.DEVICE_OVERRIDE.lower()
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
