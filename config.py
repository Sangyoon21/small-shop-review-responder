"""Central configuration: environment variables and pricing assumptions.

All prices here are *assumptions* used for estimates. They are editable in the
app sidebar and should be re-checked against the official pricing pages before
any financial decision:

- OpenAI:  https://developers.openai.com/api/docs/pricing  (formerly openai.com/api/pricing)
- Google:  https://developers.google.com/maps/billing-and-pricing/pricing

Last checked: 2026-11-06.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Small Shop Review Responder"

# --------------------------------------------------------------------------- #
# OpenAI models and pricing (USD per 1M tokens)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ModelPricing:
    label: str
    input_per_million: float
    output_per_million: float
    cached_input_per_million: float


# Reference prices supplied in the project brief; third-party trackers agreed
# with them on 2026-11-06, but the official OpenAI page could not be fetched
# directly, so treat them as configurable assumptions.
DEFAULT_MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-5.4": ModelPricing("GPT-5.4", 2.50, 15.00, 0.25),
    "gpt-5.4-mini": ModelPricing("GPT-5.4 mini", 0.75, 4.50, 0.075),
}

DEFAULT_MODEL = "gpt-5.4"

# Reasoning tokens are billed as output tokens. "low" keeps cost and latency
# down while still giving the model some room to think about tone and safety.
DEFAULT_REASONING_EFFORT = "low"
REASONING_EFFORT_OPTIONS = ["none", "low", "medium", "high"]

# --------------------------------------------------------------------------- #
# Google Places API (New) pricing (USD per 1,000 requests, 0-100k tier)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GoogleSkuPricing:
    sku: str
    price_per_thousand: float
    free_monthly_calls: int


# Billing is decided by the most expensive field in the field mask.
#  - Text Search: we request rating + userRatingCount -> "Text Search Enterprise".
#  - Place Details: we request reviews -> "Place Details Enterprise + Atmosphere".
# Source: developers.google.com/maps/billing-and-pricing/pricing (checked 2026-11-06).
DEFAULT_GOOGLE_PRICING: dict[str, GoogleSkuPricing] = {
    "text_search": GoogleSkuPricing("Places API Text Search Enterprise", 35.00, 1_000),
    "place_details": GoogleSkuPricing(
        "Places API Place Details Enterprise + Atmosphere", 25.00, 1_000
    ),
}

# --------------------------------------------------------------------------- #
# Environment
# --------------------------------------------------------------------------- #


def _env(name: str) -> str | None:
    """Read a setting from the environment / .env, then from Streamlit secrets (cloud)."""
    value = os.getenv(name)
    if value is None:
        try:
            import streamlit as st

            value = str(st.secrets.get(name, ""))
        except Exception:  # no secrets file configured
            value = ""
    value = (value or "").strip()
    return value or None


@dataclass
class Settings:
    google_maps_api_key: str | None = field(default_factory=lambda: _env("GOOGLE_MAPS_API_KEY"))
    openai_api_key: str | None = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: _env("OPENAI_MODEL") or DEFAULT_MODEL)

    @property
    def has_google_key(self) -> bool:
        return bool(self.google_maps_api_key)

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings()


# Google Places request settings
PLACES_BASE_URL = "https://places.googleapis.com/v1"
HTTP_TIMEOUT_SECONDS = 15
MAX_SEARCH_RESULTS = 10
# Rectangle loosely covering the State of Qatar, used as a *bias* (not a hard
# restriction) so "Starbucks" surfaces Doha branches first.
QATAR_LOCATION_BIAS = {
    "rectangle": {
        "low": {"latitude": 24.45, "longitude": 50.70},
        "high": {"latitude": 26.20, "longitude": 51.70},
    }
}

# OpenAI request settings
OPENAI_TIMEOUT_SECONDS = 60
MAX_OUTPUT_TOKENS = 2_500
