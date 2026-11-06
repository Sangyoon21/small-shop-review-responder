"""Google Places API (New) client: Text Search + Place Details (reviews).

Notes on compliance
-------------------
* Uses only the official Places API (New) endpoints; no scraping.
* The API returns **at most 5 reviews** per place. We never pad or fabricate.
* Field masks are kept minimal because Google bills by the most expensive
  field requested (see config.DEFAULT_GOOGLE_PRICING).
* Results are held only in the user's in-memory Streamlit session; nothing
  except place IDs should be persisted (Google Maps Platform caching terms).
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Callable

import requests

import config
from models.schemas import PlaceDetails, PlaceSummary, Review

SEARCH_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.primaryTypeDisplayName",
    ]
)

DETAILS_FIELD_MASK = ",".join(
    [
        "id",
        "displayName",
        "formattedAddress",
        "googleMapsUri",
        "websiteUri",
        "rating",
        "userRatingCount",
        "primaryTypeDisplayName",
        "editorialSummary",
        "reviews",
    ]
)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class GooglePlacesError(Exception):
    """Base error with a user-friendly message."""


class MissingGoogleApiKey(GooglePlacesError):
    pass


class GoogleQuotaError(GooglePlacesError):
    pass


class GooglePermissionError(GooglePlacesError):
    pass


class GoogleNetworkError(GooglePlacesError):
    pass


class GoogleInvalidRequest(GooglePlacesError):
    pass


class PlaceNotFound(GooglePlacesError):
    pass


def _error_from_response(resp: requests.Response) -> GooglePlacesError:
    try:
        payload = resp.json().get("error", {})
    except ValueError:
        payload = {}
    status = payload.get("status", "")
    message = payload.get("message", resp.text[:300])

    if resp.status_code == 429 or status == "RESOURCE_EXHAUSTED":
        return GoogleQuotaError(
            "Google Places quota or rate limit reached. Wait a minute, or check quotas "
            "and billing in Google Cloud Console."
        )
    if resp.status_code == 403 or status == "PERMISSION_DENIED":
        return GooglePermissionError(
            "Google rejected the API key. Check that 'Places API (New)' is enabled, billing "
            f"is active, and the key's API restrictions allow it. Google said: {message}"
        )
    if resp.status_code == 404 or status == "NOT_FOUND":
        return PlaceNotFound("That place could not be found (it may have been removed).")
    if resp.status_code == 400 or status == "INVALID_ARGUMENT":
        return GoogleInvalidRequest(f"Google rejected the request: {message}")
    return GooglePlacesError(f"Google Places error {resp.status_code}: {message}")


# --------------------------------------------------------------------------- #
# Parsing helpers (pure functions, unit-tested)
# --------------------------------------------------------------------------- #

_FRACTION_RE = re.compile(r"\.(\d+)")


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse RFC 3339 timestamps such as 2024-05-10T08:15:30.123456789Z."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    # Python only supports microseconds; trim nanoseconds.
    text = _FRACTION_RE.sub(lambda m: "." + m.group(1)[:6].ljust(6, "0"), text, count=1)
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _localized(obj: dict | None) -> tuple[str, str | None]:
    if not obj:
        return "", None
    return (obj.get("text") or "").strip(), obj.get("languageCode")


def parse_search_response(payload: dict[str, Any]) -> list[PlaceSummary]:
    places = []
    for raw in payload.get("places", []) or []:
        place_id = raw.get("id")
        if not place_id:
            continue
        name, _ = _localized(raw.get("displayName"))
        primary_type, _ = _localized(raw.get("primaryTypeDisplayName"))
        places.append(
            PlaceSummary(
                place_id=place_id,
                name=name or "(unnamed place)",
                address=raw.get("formattedAddress", ""),
                rating=raw.get("rating"),
                user_rating_count=raw.get("userRatingCount"),
                google_maps_uri=raw.get("googleMapsUri"),
                primary_type=primary_type or None,
            )
        )
    return places


def parse_review(raw: dict[str, Any], place_id: str, place_name: str, index: int) -> Review:
    original_text, original_lang = _localized(raw.get("originalText"))
    display_text, display_lang = _localized(raw.get("text"))

    # Prefer the reviewer's own words; keep Google's translation separately.
    text = original_text or display_text
    language = original_lang or display_lang
    translated_text = None
    translated_language = None
    if original_text and display_text and display_text != original_text:
        translated_text, translated_language = display_text, display_lang

    author = raw.get("authorAttribution") or {}
    rating = raw.get("rating")
    return Review(
        review_id=raw.get("name") or f"{place_id}/reviews/{index}",
        place_id=place_id,
        place_name=place_name,
        author_name=author.get("displayName") or "Google user",
        author_uri=author.get("uri"),
        author_photo_uri=author.get("photoUri"),
        rating=int(rating) if rating is not None else None,
        text=text,
        language=language,
        translated_text=translated_text,
        translated_language=translated_language,
        publish_time=parse_timestamp(raw.get("publishTime")),
        relative_time=raw.get("relativePublishTimeDescription"),
        review_uri=raw.get("googleMapsUri"),
        flag_content_uri=raw.get("flagContentUri"),
        source="google_places",
    )


def parse_details_response(payload: dict[str, Any]) -> PlaceDetails:
    place_id = payload.get("id", "")
    name, _ = _localized(payload.get("displayName"))
    name = name or "(unnamed place)"
    summary, _ = _localized(payload.get("editorialSummary"))
    primary_type, _ = _localized(payload.get("primaryTypeDisplayName"))
    reviews = [
        parse_review(r, place_id, name, i) for i, r in enumerate(payload.get("reviews", []) or [])
    ]
    return PlaceDetails(
        place_id=place_id,
        name=name,
        address=payload.get("formattedAddress", ""),
        rating=payload.get("rating"),
        user_rating_count=payload.get("userRatingCount"),
        google_maps_uri=payload.get("googleMapsUri"),
        website_uri=payload.get("websiteUri"),
        primary_type=primary_type or None,
        editorial_summary=summary or None,
        reviews=reviews,
        source="google_places",
    )


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #


class GooglePlacesClient:
    def __init__(
        self,
        api_key: str | None,
        session: requests.Session | None = None,
        on_request: Callable[[str], None] | None = None,
        max_retries: int = 2,
    ):
        if not api_key:
            raise MissingGoogleApiKey(
                "GOOGLE_MAPS_API_KEY is not set. Add it to your .env file (see README), "
                "or switch to Demo mode in the sidebar."
            )
        self._api_key = api_key
        self._session = session or requests.Session()
        self._on_request = on_request  # called with "text_search" / "place_details"
        self._max_retries = max_retries

    def _request(self, method: str, url: str, field_mask: str, kind: str, **kwargs) -> dict:
        headers = {
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": field_mask,
            "Content-Type": "application/json",
        }
        last_error: GooglePlacesError | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._session.request(
                    method, url, headers=headers, timeout=config.HTTP_TIMEOUT_SECONDS, **kwargs
                )
            except requests.Timeout as exc:
                last_error = GoogleNetworkError("Google Places timed out. Check your connection and retry.")
                last_error.__cause__ = exc
            except requests.RequestException as exc:
                last_error = GoogleNetworkError(f"Network error contacting Google Places: {exc.__class__.__name__}")
                last_error.__cause__ = exc
            else:
                # Every request that reaches Google is potentially billable.
                if self._on_request:
                    self._on_request(kind)
                if resp.ok:
                    return resp.json()
                last_error = _error_from_response(resp)
                if resp.status_code < 500:  # 4xx: retrying won't help
                    raise last_error
            if attempt < self._max_retries:
                time.sleep(0.8 * (attempt + 1))
        assert last_error is not None
        raise last_error

    def search_places(self, query: str, bias_to_qatar: bool = True) -> list[PlaceSummary]:
        query = (query or "").strip()
        if len(query) < 2:
            raise GoogleInvalidRequest("Enter at least 2 characters to search.")
        body: dict[str, Any] = {
            "textQuery": query,
            "pageSize": config.MAX_SEARCH_RESULTS,
            "languageCode": "en",
        }
        if bias_to_qatar:
            body["regionCode"] = "QA"
            body["locationBias"] = config.QATAR_LOCATION_BIAS
        payload = self._request(
            "POST",
            f"{config.PLACES_BASE_URL}/places:searchText",
            SEARCH_FIELD_MASK,
            "text_search",
            json=body,
        )
        return parse_search_response(payload)

    def get_place_details(self, place_id: str, language: str = "en") -> PlaceDetails:
        if not place_id:
            raise GoogleInvalidRequest("No place selected.")
        payload = self._request(
            "GET",
            f"{config.PLACES_BASE_URL}/places/{place_id}",
            DETAILS_FIELD_MASK,
            "place_details",
            params={"languageCode": language},
        )
        return parse_details_response(payload)
