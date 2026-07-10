"""Project settings via environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings:
    """Minimal settings - reads .env via python-dotenv (no pydantic-settings)."""

    openai_api_key: str
    golden_records_path: Path

    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        raw_path = os.getenv(
            "GOLDEN_RECORDS_PATH",
            "golden_records/golden records.csv",
        )
        path = Path(raw_path)
        self.golden_records_path = (
            path if path.is_absolute() else _PROJECT_ROOT / path
        )


def get_settings() -> Settings:
    return Settings()
