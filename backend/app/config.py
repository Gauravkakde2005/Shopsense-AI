from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(dotenv_path: str | Path | None = None, **kwargs: object) -> bool:
        path = Path(dotenv_path) if dotenv_path else Path(".env")
        if not path.exists():
            return False
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#") or "=" not in entry:
                continue
            key, value = entry.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return True


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


PRODUCT_SEARCH_PROVIDER = os.getenv("PRODUCT_SEARCH_PROVIDER", "serpapi").strip().lower()
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()
SERPAPI_LOCATION = os.getenv("SERPAPI_LOCATION", "India").strip()
SERPAPI_RESULT_LIMIT = int(os.getenv("SERPAPI_RESULT_LIMIT", "10"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_API_BASE_URL = os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
AI_REQUEST_TIMEOUT_SECONDS = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "20"))


def provider_status() -> dict[str, str]:
    return {
        "product_search": PRODUCT_SEARCH_PROVIDER,
        "product_search_status": "configured" if SERPAPI_KEY else "missing_api_key",
        "llm_provider": "groq",
        "llm_status": "configured" if GROQ_API_KEY else "optional_not_configured",
        "source_policy": "authorized_provider_only",
    }