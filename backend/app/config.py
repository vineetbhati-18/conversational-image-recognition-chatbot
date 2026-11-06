from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import torch


class Settings(BaseSettings):
    """
    Application Settings configured via environment variables or default fallbacks.
    """
    APP_NAME: str = "BEL Conversational Image Recognition Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server Bindings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "bhati"
    DB_PASSWORD: str = ""
    DB_NAME: str = "bel_chatbot_db"

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_PASSWORD:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql+asyncpg://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.DB_PASSWORD:
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # AI / ML Inference Configuration
    DEVICE_OVERRIDE: str = ""
    YOLO_MODEL_NAME: str = "yolov8s.pt"
    VQA_MODEL_NAME: str = "Salesforce/blip-vqa-base"
    CONFIDENCE_THRESHOLD: float = 0.35
    MAX_UPLOAD_SIZE_MB: int = 15

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "uploads"

    @property
    def INFERENCE_DEVICE(self) -> str:
        """
        Determines the optimal PyTorch compute device:
        - Prefers Apple Silicon MPS if on macOS with Apple GPU
        - CUDA if available
        - Defaults to CPU
        """
        if self.DEVICE_OVERRIDE:
            return self.DEVICE_OVERRIDE
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
