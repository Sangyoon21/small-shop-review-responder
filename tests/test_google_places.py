"""Google Places parsing and client tests, using mocked HTTP responses only."""

from unittest.mock import MagicMock

import pytest
import requests

from services import google_places as gp

SEARCH_PAYLOAD = {
    "places": [
        {
            "id": "ChIJ_flatwhite",
            "displayName": {"text": "Flat White Specialty Coffee", "languageCode": "en"},
            "formattedAddress": "Al Sadd St, Doha, Qatar",
            "googleMapsUri": "https://maps.google.com/?cid=1",
            "rating": 4.6,
            "userRatingCount": 1234,
            "primaryTypeDisplayName": {"text": "Coffee shop", "languageCode": "en"},
        },
        {"displayName": {"text": "No id -> skipped"}},
        {"id": "ChIJ_minimal"},
    ]
}

DETAILS_PAYLOAD = {
    "id": "ChIJ_flatwhite",
    "displayName": {"text": "Flat White Specialty Coffee"},
    "formattedAddress": "Al Sadd St, Doha, Qatar",
    "googleMapsUri": "https://maps.google.com/?cid=1",
    "rating": 4.6,
    "userRatingCount": 1234,
    "editorialSummary": {"text": "Specialty coffee roaster."},
    "reviews": [
        {
            "name": "places/ChIJ_flatwhite/reviews/abc",
            "relativePublishTimeDescription": "2 weeks ago",
            "rating": 5,
            "text": {"text": "Great flat white!", "languageCode": "en"},
            "originalText": {"text": "Great flat white!", "languageCode": "en"},
            "authorAttribution": {
                "displayName": "Aisha R.",
                "uri": "https://www.google.com/maps/contrib/1",
                "photoUri": "https://lh3.googleusercontent.com/a.png",
            },
            "publishTime": "2026-10-20T08:15:30.123456789Z",
            "googleMapsUri": "https://www.google.com/maps/reviews/abc",
            "flagContentUri": "https://www.google.com/local/review/rap/report?abc",
        },
        {
            "name": "places/ChIJ_flatwhite/reviews/def",
            "rating": 2,
            "text": {"text": "The coffee was cold.", "languageCode": "en"},
            "originalText": {"text": "القهوة كانت باردة.", "languageCode": "ar"},
            "authorAttribution": {"displayName": "Omar"},
            "publishTime": "2026-09-01T10:00:00Z",
        },
        {
            # Rating-only review: no text fields at all.
            "name": "places/ChIJ_flatwhite/reviews/ghi",
            "rating": 4,
            "authorAttribution": {"displayName": "Guest"},
        },
    ],
}


# ---- parsing ---------------------------------------------------------------- #


def test_parse_search_response_extracts_fields_and_skips_missing_ids():
    places = gp.parse_search_response(SEARCH_PAYLOAD)
    assert [p.place_id for p in places] == ["ChIJ_flatwhite", "ChIJ_minimal"]
    first = places[0]
    assert first.name == "Flat White Specialty Coffee"
    assert first.address == "Al Sadd St, Doha, Qatar"
    assert first.rating == 4.6
    assert first.user_rating_count == 1234
    assert first.google_maps_uri.startswith("https://maps.google.com")
    assert first.primary_type == "Coffee shop"
    assert places[1].name == "(unnamed place)"
    assert places[1].rating is None


def test_parse_search_response_handles_empty_payload():
    assert gp.parse_search_response({}) == []
    assert gp.parse_search_response({"places": None}) == []


def test_parse_details_extracts_reviews():
    details = gp.parse_details_response(DETAILS_PAYLOAD)
    assert details.name == "Flat White Specialty Coffee"
    assert details.user_rating_count == 1234
    assert details.editorial_summary == "Specialty coffee roaster."
    assert len(details.reviews) == 3

    r = details.reviews[0]
    assert r.review_id == "places/ChIJ_flatwhite/reviews/abc"
    assert r.place_id == "ChIJ_flatwhite"
    assert r.place_name == "Flat White Specialty Coffee"
    assert r.author_name == "Aisha R."
    assert r.author_uri.endswith("/contrib/1")
    assert r.rating == 5
    assert r.text == "Great flat white!"
    assert r.language == "en"
    assert r.translated_text is None  # identical to original -> no translation stored
    assert r.review_uri == "https://www.google.com/maps/reviews/abc"
    assert r.publish_time.year == 2026 and r.publish_time.microsecond == 123456
    assert r.relative_time == "2 weeks ago"
    assert r.source == "google_places"


def test_original_language_text_is_preferred_over_translation():
    r = gp.parse_details_response(DETAILS_PAYLOAD).reviews[1]
    assert r.text == "القهوة كانت باردة."
    assert r.language == "ar"
    assert r.translated_text == "The coffee was cold."
    assert r.translated_language == "en"


def test_review_without_text_is_kept_not_fabricated():
    r = gp.parse_details_response(DETAILS_PAYLOAD).reviews[2]
    assert r.text == ""
    assert r.has_text is False
    assert r.rating == 4
    assert r.publish_time is None


def test_place_with_no_reviews_returns_empty_list():
    payload = {k: v for k, v in DETAILS_PAYLOAD.items() if k != "reviews"}
    details = gp.parse_details_response(payload)
    assert details.reviews == []


@pytest.mark.parametrize(
    "value,ok",
    [
        ("2026-10-20T08:15:30Z", True),
        ("2026-10-20T08:15:30.5Z", True),
        ("2026-10-20T08:15:30.123456789Z", True),
        ("not a date", False),
        (None, False),
    ],
)
def test_parse_timestamp(value, ok):
    assert (gp.parse_timestamp(value) is not None) is ok


def test_field_masks_are_minimal_and_include_required_fields():
    for field in ["places.id", "places.displayName", "places.formattedAddress", "places.rating",
                  "places.userRatingCount", "places.googleMapsUri"]:
        assert field in gp.SEARCH_FIELD_MASK
    assert "reviews" not in gp.SEARCH_FIELD_MASK  # avoids the Atmosphere SKU on search
    assert "*" not in gp.SEARCH_FIELD_MASK and "*" not in gp.DETAILS_FIELD_MASK
    assert "reviews" in gp.DETAILS_FIELD_MASK.split(",")


# ---- client ------------------------------------------------------------------ #


def _response(status: int, payload: dict) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.ok = 200 <= status < 300
    resp.json.return_value = payload
    resp.text = str(payload)
    return resp


def test_missing_api_key_raises():
    with pytest.raises(gp.MissingGoogleApiKey):
        gp.GooglePlacesClient(None)
    with pytest.raises(gp.MissingGoogleApiKey):
        gp.GooglePlacesClient("")


def test_search_sends_field_mask_and_counts_request():
    session = MagicMock()
    session.request.return_value = _response(200, SEARCH_PAYLOAD)
    counted = []
    client = gp.GooglePlacesClient("test-key", session=session, on_request=counted.append)

    places = client.search_places("Flat White Qatar")

    assert len(places) == 2
    method, url = session.request.call_args.args
    kwargs = session.request.call_args.kwargs
    assert method == "POST" and url.endswith("/places:searchText")
    assert kwargs["headers"]["X-Goog-FieldMask"] == gp.SEARCH_FIELD_MASK
    assert kwargs["headers"]["X-Goog-Api-Key"] == "test-key"
    assert kwargs["json"]["textQuery"] == "Flat White Qatar"
    assert kwargs["json"]["regionCode"] == "QA"
    assert counted == ["text_search"]


def test_details_request_uses_place_id_and_counts():
    session = MagicMock()
    session.request.return_value = _response(200, DETAILS_PAYLOAD)
    counted = []
    client = gp.GooglePlacesClient("k", session=session, on_request=counted.append)
    details = client.get_place_details("ChIJ_flatwhite")
    assert details.place_id == "ChIJ_flatwhite"
    assert session.request.call_args.args[1].endswith("/places/ChIJ_flatwhite")
    assert counted == ["place_details"]


def test_short_query_is_rejected_without_calling_api():
    session = MagicMock()
    client = gp.GooglePlacesClient("k", session=session)
    with pytest.raises(gp.GoogleInvalidRequest):
        client.search_places(" a ")
    session.request.assert_not_called()


@pytest.mark.parametrize(
    "status,payload,exc",
    [
        (429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded"}}, gp.GoogleQuotaError),
        (403, {"error": {"status": "PERMISSION_DENIED", "message": "API not enabled"}}, gp.GooglePermissionError),
        (400, {"error": {"status": "INVALID_ARGUMENT", "message": "bad"}}, gp.GoogleInvalidRequest),
        (404, {"error": {"status": "NOT_FOUND", "message": "gone"}}, gp.PlaceNotFound),
    ],
)
def test_client_error_mapping_does_not_retry_4xx(status, payload, exc):
    session = MagicMock()
    session.request.return_value = _response(status, payload)
    client = gp.GooglePlacesClient("k", session=session)
    with pytest.raises(exc):
        client.search_places("Starbucks Doha")
    assert session.request.call_count == 1


def test_network_error_is_retried_then_raised(monkeypatch):
    monkeypatch.setattr(gp.time, "sleep", lambda _: None)
    session = MagicMock()
    session.request.side_effect = requests.ConnectionError("down")
    counted = []
    client = gp.GooglePlacesClient("k", session=session, on_request=counted.append, max_retries=2)
    with pytest.raises(gp.GoogleNetworkError):
        client.search_places("Starbucks Doha")
    assert session.request.call_count == 3
    assert counted == []  # nothing reached Google, nothing billable counted


def test_server_error_then_success(monkeypatch):
    monkeypatch.setattr(gp.time, "sleep", lambda _: None)
    session = MagicMock()
    session.request.side_effect = [_response(503, {"error": {"message": "busy"}}), _response(200, SEARCH_PAYLOAD)]
    client = gp.GooglePlacesClient("k", session=session)
    assert len(client.search_places("Starbucks Doha")) == 2
