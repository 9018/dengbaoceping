from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    BASE_DIR: Path = BASE_DIR
    APP_NAME: str = "CPGJ Tool Backend"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    SECRET_KEY: str = "replace-this-in-production"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'app.db'}"
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    EXPORT_DIR: str = str(BASE_DIR / "exports")
    SNAPSHOT_DIR: str = str(BASE_DIR / "snapshots")
    GUIDANCE_FILE_PATH: str = str(BASE_DIR.parent / "md" / "指导书.md")
    OCR_PROVIDER: str = "mock"
    OCR_TIMEOUT_SECONDS: int = 30
    PADDLE_OCR_LANG: str = "ch"
    PADDLE_OCR_USE_ANGLE_CLS: bool = True
    PADDLE_OCR_USE_GPU: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
