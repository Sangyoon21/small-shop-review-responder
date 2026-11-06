"""Streamlit session-state helpers.

Everything lives in st.session_state (in memory, per browser session), so drafts
survive Streamlit reruns and nothing from Google is written to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import streamlit as st

from models.schemas import ReviewAnalysis
from services.cost_tracker import CostTracker

ReplyStatus = Literal["none", "draft", "approved", "rejected"]


@dataclass
class ReviewState:
    analysis: ReviewAnalysis | None = None
    analysis_origin: Literal["live", "sample"] | None = None  # sample = pre-written demo output
    draft: str = ""
    draft_origin: Literal["live", "sample", "edited"] | None = None
    history: list[str] = field(default_factory=list)
    status: ReplyStatus = "none"
    approved_text: str = ""
    editing: bool = False
    error: str | None = None
    notice: str | None = None


def init_state() -> None:
    defaults = {
        "tracker": CostTracker(),
        "search_results": [],
        "place": None,
        "review_states": {},
        "data_mode": "Live Google Maps",
        "biz_description": "",
        "biz_approved_info": "",
        "biz_signature": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def tracker() -> CostTracker:
    return st.session_state["tracker"]


def review_state(review_id: str) -> ReviewState:
    states: dict[str, ReviewState] = st.session_state["review_states"]
    if review_id not in states:
        states[review_id] = ReviewState()
    return states[review_id]


def clear_place() -> None:
    st.session_state["place"] = None
    st.session_state["review_states"] = {}
