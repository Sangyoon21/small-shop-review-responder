"""Headless UI smoke tests using Streamlit's AppTest (no network, no API keys)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    # Empty values stop python-dotenv from loading real keys from a local .env.
    for key in ("GOOGLE_MAPS_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4")


def _button(at: AppTest, label: str):
    matches = [b for b in at.button if b.label == label]
    assert matches, f"button {label!r} not found; have {[b.label for b in at.button]}"
    return matches[0]


def test_without_keys_app_opens_in_demo_mode():
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    assert at.session_state["data_mode"] == "Demo (synthetic data)"
    assert at.session_state["place"].source == "demo_synthetic"


def test_live_mode_without_keys_shows_guidance():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Live Google Maps").run()
    assert not at.exception
    errors = " ".join(e.value for e in at.sidebar.error)
    assert "GOOGLE_MAPS_API_KEY" in errors
    # No business loaded, no fabricated data.
    assert at.session_state["place"] is None


def test_demo_flow_analyze_edit_approve():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Demo (synthetic data)").run()
    assert not at.exception
    place = at.session_state["place"]
    assert place.source == "demo_synthetic"
    assert len(place.reviews) == 5

    _button(at, "Analyze all reviews").click().run()
    assert not at.exception
    states = at.session_state["review_states"]
    assert len(states) == 5
    assert all(s.analysis is not None and s.analysis_origin == "sample" for s in states.values())
    flagged = [s for s in states.values() if s.analysis.needs_owner_attention]
    assert len(flagged) >= 2  # food safety + rude staff

    # Approve the first card's draft (cards are priority-sorted).
    _button(at, "Approve").click().run()
    assert not at.exception
    assert sum(s.status == "approved" for s in at.session_state["review_states"].values()) == 1

    # Edit another draft and save it.
    _button(at, "Edit").click().run()
    edit_areas = [t for t in at.text_area if t.key and t.key.startswith("edit_")]
    assert len(edit_areas) == 1
    edit_areas[0].set_value("Thank you, we hope to see you again soon.").run()
    _button(at, "Save edits").click().run()
    assert not at.exception
    edited = [s for s in at.session_state["review_states"].values() if s.draft_origin == "edited"]
    assert len(edited) == 1 and edited[0].history  # original kept in history


def test_switching_back_to_live_clears_demo_data():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Demo (synthetic data)").run()
    at.sidebar.radio[0].set_value("Live Google Maps").run()
    assert not at.exception
    assert at.session_state["place"] is None
    assert at.session_state["review_states"] == {}


def test_live_flow_with_mocked_google_and_openai(monkeypatch):
    """Search -> load -> analyze -> regenerate, with HTTP and OpenAI SDK mocked."""
    from unittest.mock import MagicMock

    import requests

    from services import ai_analyzer
    from services import google_places
    from tests.test_ai_analyzer import analysis_dict, fake_response
    from tests.test_google_places import DETAILS_PAYLOAD, SEARCH_PAYLOAD

    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "fake-google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")

    def fake_http(method, url, **kwargs):
        resp = MagicMock(spec=requests.Response)
        resp.status_code, resp.ok = 200, True
        resp.json.return_value = SEARCH_PAYLOAD if url.endswith(":searchText") else DETAILS_PAYLOAD
        return resp

    session = MagicMock()
    session.request.side_effect = fake_http
    monkeypatch.setattr(google_places.requests, "Session", lambda: session)

    def fake_create(**kwargs):
        arabic = "ARABIC only" in kwargs["input"]
        if kwargs["text"]["format"]["name"] == "review_analysis":
            return fake_response(analysis_dict(
                suggested_response="مسودة أولى." if arabic else "First draft.",
                suggested_response_language="ar" if arabic else "en",
            ))
        return fake_response({"reply": "رد جديد." if arabic else "A regenerated reply.",
                              "language": "ar" if arabic else "en"})

    client = MagicMock()
    client.responses.create.side_effect = fake_create
    monkeypatch.setattr(ai_analyzer.openai, "OpenAI", lambda **kw: client)

    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.text_input[0].set_value("Flat White Qatar")
    [b for b in at.sidebar.button if b.label == "Search Google Maps"][0].click().run()
    assert not at.exception
    assert len(at.session_state["search_results"]) == 2

    [b for b in at.sidebar.button if b.label == "Load reviews"][0].click().run()
    assert not at.exception
    place = at.session_state["place"]
    assert place.source == "google_places" and len(place.reviews) == 3
    assert at.session_state["tracker"].google_requests == {"text_search": 1, "place_details": 1}

    _button(at, "Analyze all reviews").click().run()
    assert not at.exception
    states = at.session_state["review_states"]
    assert all(s.analysis_origin == "live" for s in states.values())
    # The Arabic review got an Arabic draft; the English ones got English drafts.
    assert sorted(s.draft for s in states.values()) == sorted(["First draft.", "First draft.", "مسودة أولى."])
    assert at.session_state["tracker"].openai_request_count == 3

    _button(at, "Regenerate").click().run()
    assert not at.exception
    regenerated = [s for s in at.session_state["review_states"].values() if s.history]
    assert len(regenerated) == 1
    assert (regenerated[0].history, regenerated[0].draft) in [
        (["First draft."], "A regenerated reply."), (["مسودة أولى."], "رد جديد.")]
    assert at.session_state["tracker"].openai_request_count == 4


def _arabic(text: str) -> bool:
    from services.ai_analyzer import is_arabic
    return is_arabic(text)


def test_demo_follows_reply_language_rule():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Demo (synthetic data)").run()
    _button(at, "Analyze all reviews").click().run()
    place = at.session_state["place"]
    states = at.session_state["review_states"]
    # Default: Arabic review -> Arabic reply, English review -> English reply.
    for review in place.reviews:
        assert _arabic(states[review.review_id].draft) == _arabic(review.text)


def test_demo_language_setting_changes_replies():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Demo (synthetic data)").run()
    at.sidebar.selectbox(key="language_mode").set_value("en").run()
    _button(at, "Analyze all reviews").click().run()
    assert not any(_arabic(s.draft) for s in at.session_state["review_states"].values())

    # Switch to Arabic and regenerate one reply: it switches to the Arabic version.
    at.sidebar.selectbox(key="language_mode").set_value("ar").run()
    _button(at, "Regenerate").click().run()
    assert not at.exception
    switched = [s for s in at.session_state["review_states"].values() if _arabic(s.draft)]
    assert len(switched) == 1 and switched[0].history and not _arabic(switched[0].history[-1])


def test_demo_regenerate_gives_a_different_reply_each_time():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Demo (synthetic data)").run()
    _button(at, "Analyze all reviews").click().run()
    states = at.session_state["review_states"]
    before = {rid: s.draft for rid, s in states.items()}

    _button(at, "Regenerate").click().run()   # first card
    assert not at.exception
    changed = [rid for rid, s in at.session_state["review_states"].items() if s.draft != before[rid]]
    assert len(changed) == 1
    rid = changed[0]
    second = at.session_state["review_states"][rid].draft
    assert at.session_state["review_states"][rid].error is None

    _button(at, "Regenerate").click().run()
    third = at.session_state["review_states"][rid].draft
    assert third != second and third == before[rid]  # cycles between the two versions
    assert at.session_state["review_states"][rid].history == [before[rid], second]


def test_demo_tone_setting_changes_reply():
    from services.demo_replies import DEMO_REPLY_VARIANTS

    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value("Demo (synthetic data)").run()
    at.session_state["tone"] = "formal"
    at.run()
    _button(at, "Analyze all reviews").click().run()
    assert not at.exception
    formal = {v for langs in DEMO_REPLY_VARIANTS.values() for tones in langs.values() for v in tones["formal"]}
    assert all(s.draft in formal for s in at.session_state["review_states"].values())
