"""Project settings via environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else _PROJECT_ROOT / path


class Settings:
    """Minimal settings - reads .env via python-dotenv (no pydantic-settings)."""

    openai_api_key: str
    golden_records_path: Path
    documents_path: Path
    # Mean chars/page below this => scanned (doc 01 ~1378, doc 07 ~0).
    text_density_threshold: float
    scan_image_resolution: int

    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.golden_records_path = _resolve_path(
            os.getenv(
                "GOLDEN_RECORDS_PATH",
                "golden_records/golden records.csv",
            )
        )
        self.documents_path = _resolve_path(
            os.getenv("DOCUMENTS_PATH", "documents")
        )
        self.text_density_threshold = float(
            os.getenv("TEXT_DENSITY_THRESHOLD", "50.0")
        )
        self.scan_image_resolution = int(
            os.getenv("SCAN_IMAGE_RESOLUTION", "150")
        )


def get_settings() -> Settings:
    return Settings()
