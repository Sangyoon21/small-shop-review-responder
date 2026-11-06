"""Charts for the *retrieved review sample* (max 5 reviews from the Places API)."""

from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from models.schemas import PlaceDetails
from state import ReviewState

SENTIMENT_COLORS = {"positive": "#2E7D5B", "mixed": "#D9A21B", "negative": "#B3261E"}
BRAND = "#8A1538"
FONT = dict(family="Inter, system-ui, sans-serif", size=13)


def _layout(fig: go.Figure, height: int = 280) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        font=FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def sample_stats(place: PlaceDetails, states: dict[str, ReviewState]) -> dict:
    """Pure helper (also used by the metric row)."""
    analyses = [states[r.review_id].analysis for r in place.reviews
                if r.review_id in states and states[r.review_id].analysis is not None]
    sentiments = Counter(a.sentiment for a in analyses)
    return {
        "retrieved": len(place.reviews),
        "analyzed": len(analyses),
        "positive": sentiments.get("positive", 0),
        "mixed": sentiments.get("mixed", 0),
        "negative": sentiments.get("negative", 0),
        "attention": sum(1 for a in analyses if a.needs_owner_attention),
        "low_star": sum(1 for r in place.reviews if r.rating is not None and r.rating <= 2),
    }


def render_analytics(place: PlaceDetails, states: dict[str, ReviewState]) -> None:
    n = len(place.reviews)
    st.info(
        f"These charts describe only the **{n} review{'s' if n != 1 else ''}** returned by the Google "
        f"Places API (the API returns at most 5, chosen by Google). They are **not** representative of "
        f"all {place.user_rating_count or 'the'} Google ratings for this business.",
        icon=":material/info:",
    )
    if n == 0:
        st.caption("No reviews to chart.")
        return

    stats = sample_stats(place, states)
    analyses = [(r, states[r.review_id].analysis) for r in place.reviews
                if r.review_id in states and states[r.review_id].analysis is not None]

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**Star ratings in sample**")
            counts = Counter(r.rating for r in place.reviews if r.rating is not None)
            df = pd.DataFrame({"Stars": [f"{s}★" for s in range(1, 6)], "Reviews": [counts.get(s, 0) for s in range(1, 6)]})
            fig = px.bar(df, x="Stars", y="Reviews", color_discrete_sequence=[BRAND])
            fig.update_yaxes(dtick=1, gridcolor="rgba(128,128,128,0.2)")
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(_layout(fig), width="stretch", config={"displayModeBar": False})
    with c2:
        with st.container(border=True):
            st.markdown(f"**AI sentiment** · {stats['analyzed']} of {n} analyzed")
            if stats["analyzed"] == 0:
                st.caption("Run **Analyze all reviews** to see sentiment.")
            else:
                labels = ["positive", "mixed", "negative"]
                values = [stats[k] for k in labels]
                fig = go.Figure(go.Pie(
                    labels=[l.title() for l in labels], values=values, hole=0.6,
                    marker=dict(colors=[SENTIMENT_COLORS[l] for l in labels]),
                    textinfo="label+value", sort=False,
                ))
                st.plotly_chart(_layout(fig), width="stretch", config={"displayModeBar": False})

    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.markdown("**Common complaint themes**")
            cats = Counter(c for _, a in analyses for c in a.complaint_categories)
            if not cats:
                st.caption("No complaints found in analyzed reviews yet.")
            else:
                df = pd.DataFrame(
                    [{"Theme": k.replace("_", " ").title(), "Mentions": v} for k, v in cats.most_common()]
                ).sort_values("Mentions")
                fig = px.bar(df, x="Mentions", y="Theme", orientation="h", color_discrete_sequence=[BRAND])
                fig.update_xaxes(dtick=1, gridcolor="rgba(128,128,128,0.2)")
                st.plotly_chart(_layout(fig, 60 + 36 * len(df)), width="stretch", config={"displayModeBar": False})
    with c4:
        with st.container(border=True):
            st.markdown("**High-priority reviews**")
            rows = [
                {
                    "Reviewer": r.author_name,
                    "Stars": r.rating,
                    "Urgency": a.urgency,
                    "Flags": ", ".join(f.replace("_", " ") for f in a.sensitive_flags) or "—",
                    "Why": a.attention_reason or "—",
                }
                for r, a in analyses
                if a.needs_owner_attention or a.urgency == "high"
            ]
            if not rows:
                st.caption("No reviews currently flagged for owner attention.")
            else:
                order = {"high": 0, "medium": 1, "low": 2}
                rows.sort(key=lambda x: (order[x["Urgency"]], x["Stars"] or 0))
                st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
