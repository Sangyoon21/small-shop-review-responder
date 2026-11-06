"""Pydantic schemas for places, reviews, and validated LLM output."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Google Places data
# --------------------------------------------------------------------------- #


class PlaceSummary(BaseModel):
    """A business returned by Text Search."""

    place_id: str
    name: str
    address: str = ""
    rating: float | None = None
    user_rating_count: int | None = None
    google_maps_uri: str | None = None
    primary_type: str | None = None


class Review(BaseModel):
    """A single public review. `source` distinguishes real Google data from demo data."""

    review_id: str
    place_id: str
    place_name: str
    author_name: str = "Google user"
    author_uri: str | None = None
    author_photo_uri: str | None = None
    rating: int | None = None
    text: str = ""  # original-language text when available
    language: str | None = None
    translated_text: str | None = None  # Google's translation, if different
    translated_language: str | None = None
    publish_time: datetime | None = None
    relative_time: str | None = None
    review_uri: str | None = None
    flag_content_uri: str | None = None
    source: Literal["google_places", "demo_synthetic"] = "google_places"

    @property
    def has_text(self) -> bool:
        return bool(self.text.strip())


class PlaceDetails(BaseModel):
    place_id: str
    name: str
    address: str = ""
    rating: float | None = None
    user_rating_count: int | None = None
    google_maps_uri: str | None = None
    website_uri: str | None = None
    primary_type: str | None = None
    editorial_summary: str | None = None
    reviews: list[Review] = Field(default_factory=list)
    source: Literal["google_places", "demo_synthetic"] = "google_places"


# --------------------------------------------------------------------------- #
# LLM structured output
# --------------------------------------------------------------------------- #
# All fields are required with no defaults so the JSON schema is compatible with
# OpenAI strict structured outputs; `extra="forbid"` -> additionalProperties: false.

Sentiment = Literal["positive", "mixed", "negative"]
Urgency = Literal["low", "medium", "high"]
SensitiveFlag = Literal[
    "food_safety",
    "harassment",
    "discrimination",
    "staff_misconduct",
    "health_or_injury",
    "legal_threat",
    "privacy",
]
ComplaintCategory = Literal[
    "food_quality",
    "service_speed",
    "staff_attitude",
    "price_value",
    "cleanliness",
    "order_accuracy",
    "ambience",
    "food_safety",
    "portion_size",
    "delivery",
    "other",
]


class ReviewAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sentiment: Sentiment
    urgency: Urgency
    detected_language: str = Field(description="ISO 639-1 code of the review, e.g. 'en' or 'ar'.")
    key_complaints: list[str] = Field(description="Short phrases quoting/paraphrasing ONLY what the reviewer said.")
    complaint_categories: list[ComplaintCategory]
    positive_feedback: list[str]
    actionable_insights: list[str] = Field(description="Internal suggestions for the owner (not public).")
    sensitive_flags: list[SensitiveFlag]
    needs_owner_attention: bool
    attention_reason: str = Field(description="Why the owner must look at this personally; empty string if not needed.")
    suggested_response: str = Field(description="Draft public reply in the language given in <reply_settings>.")
    suggested_response_language: str = Field(description="ISO 639-1 code of suggested_response, e.g. 'en' or 'ar'.")


class ReplyDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str
    language: str = Field(description="ISO 639-1 code of the reply.")


def strict_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return a JSON schema accepted by OpenAI strict structured outputs.

    Ensures every object lists all properties as required and forbids extras,
    including nested `$defs`.
    """
    schema = model.model_json_schema()

    def _fix(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            node.pop("default", None)
            for value in node.values():
                _fix(value)
        elif isinstance(node, list):
            for item in node:
                _fix(item)

    _fix(schema)
    return schema
