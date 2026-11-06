"""API usage, cost estimates and the business simulation panel.

Separate from analytics.py because it describes *our* operating costs, not the
customer's reviews.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import GoogleSkuPricing, ModelPricing
from services.cost_tracker import CostTracker, SimulationInputs, simulate_monthly


def _usd(x: float, digits: int = 4) -> str:
    return f"${x:,.{digits}f}"


def render_cost_section(
    tracker: CostTracker,
    model_pricing: dict[str, ModelPricing],
    google_pricing: dict[str, GoogleSkuPricing],
    selected_model: str,
) -> None:
    st.markdown("#### Measured usage this session")
    st.caption(
        "Token counts and request counts below are **measured** from real API responses in this "
        "browser session. Dollar figures are **estimates** from the price assumptions in the sidebar."
    )

    c = st.columns(4)
    c[0].metric("OpenAI requests", tracker.openai_request_count,
                help=f"{tracker.failed_openai_requests} failed request(s) not counted.")
    c[1].metric("Input tokens", f"{tracker.input_tokens:,}",
                help=f"Of which cached: {tracker.cached_input_tokens:,}")
    c[2].metric("Output tokens", f"{tracker.output_tokens:,}",
                help=f"Includes {tracker.reasoning_tokens:,} reasoning tokens (billed as output).")
    c[3].metric("Est. OpenAI cost", _usd(tracker.openai_cost(model_pricing)))

    g = st.columns(4)
    g[0].metric("Google Text Search requests", tracker.google_requests.get("text_search", 0))
    g[1].metric("Google Place Details requests", tracker.google_requests.get("place_details", 0))
    g[2].metric("Est. Google cost (list price)", _usd(tracker.google_cost(google_pricing)),
                help="Before Google's monthly free usage caps. Your real bill may be $0 within the caps.")
    g[3].metric("Est. combined API cost", _usd(tracker.total_cost(model_pricing, google_pricing)))

    breakdown = tracker.per_model_breakdown(model_pricing)
    if breakdown:
        df = pd.DataFrame(breakdown)
        df["estimated_cost_usd"] = df["estimated_cost_usd"].map(lambda v: round(v, 5))
        st.dataframe(df, hide_index=True, width="stretch")

    with st.expander("Pricing assumptions used", icon=":material/receipt_long:"):
        rows = [
            {"Item": f"OpenAI {p.label}", "Unit": "per 1M tokens",
             "Input": p.input_per_million, "Cached input": p.cached_input_per_million, "Output": p.output_per_million}
            for p in model_pricing.values()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        grows = [
            {"SKU": s.sku, "USD per 1,000 requests": s.price_per_thousand, "Free requests / month": s.free_monthly_calls}
            for s in google_pricing.values()
        ]
        st.dataframe(pd.DataFrame(grows), hide_index=True, width="stretch")
        st.caption(
            "Google bills by the most expensive field requested: rating fields put Text Search in the "
            "Enterprise SKU, and the `reviews` field puts Place Details in Enterprise + Atmosphere. "
            "Prices last checked 2026-11-06. Verify at developers.google.com/maps/billing-and-pricing/pricing "
            "and the OpenAI pricing page before relying on them."
        )

    st.divider()
    _render_simulation(tracker, model_pricing, google_pricing, selected_model)


def _render_simulation(
    tracker: CostTracker,
    model_pricing: dict[str, ModelPricing],
    google_pricing: dict[str, GoogleSkuPricing],
    selected_model: str,
) -> None:
    st.markdown("#### Monthly business simulation")
    st.caption(
        "A what-if model of subscription revenue vs. API costs. It excludes salaries, hosting, "
        "marketing, payment fees and taxes, so the result is **not** profit."
    )

    # Default per-review token usage from this session's real calls, if any.
    calls = tracker.openai_calls
    if calls:
        default_in = int(sum(c.input_tokens for c in calls) / len(calls)) * 2
        default_out = int(sum(c.output_tokens for c in calls) / len(calls)) * 2
        source_note = "Defaults derived from this session's measured average × 2 calls (analysis + reply)."
    else:
        default_in, default_out = 3_000, 1_500
        source_note = "Defaults are assumptions (no AI calls measured yet): ~2 calls per review."

    left, right = st.columns([1, 1.2], gap="large")
    with left:
        restaurants = st.number_input("Subscribing restaurants", 1, 100_000, 50, step=10)
        reviews = st.number_input("Reviews analyzed per restaurant / month", 0, 10_000, 40, step=5)
        price = st.number_input("Monthly subscription price (USD)", 0.0, 10_000.0, 29.0, step=1.0)
        model_key = st.selectbox(
            "Model", list(model_pricing), index=list(model_pricing).index(selected_model)
            if selected_model in model_pricing else 0,
            format_func=lambda k: model_pricing[k].label, key="sim_model",
        )
        tin = st.number_input("Avg input tokens per review", 0, 200_000, default_in, step=100)
        tout = st.number_input("Avg output tokens per review", 0, 200_000, default_out, step=100)
        details = st.number_input("Google review refreshes per restaurant / month", 0, 10_000, 30, step=5,
                                  help="Each refresh is one Place Details (Enterprise + Atmosphere) request.")
        free_cap = st.toggle("Subtract Google's monthly free requests", value=False,
                             help="Conservative default is off.")
        st.caption(source_note)

    sku = google_pricing["place_details"]
    result = simulate_monthly(
        SimulationInputs(
            restaurants=int(restaurants),
            reviews_per_restaurant=int(reviews),
            subscription_price=float(price),
            avg_input_tokens_per_review=int(tin),
            avg_output_tokens_per_review=int(tout),
            model_pricing=model_pricing[model_key],
            google_details_requests_per_restaurant=int(details),
            google_details_price_per_thousand=sku.price_per_thousand,
            google_free_monthly_calls=sku.free_monthly_calls if free_cap else 0,
        )
    )
    with right:
        with st.container(border=True):
            a, b = st.columns(2)
            a.metric("Est. monthly revenue", _usd(result.monthly_revenue, 0))
            b.metric("Est. monthly API costs", _usd(result.monthly_api_cost, 2))
            a.metric("OpenAI", _usd(result.monthly_ai_cost, 2))
            b.metric("Google Places", _usd(result.monthly_google_cost, 2))
            a.metric("Revenue after API costs", _usd(result.revenue_after_api_costs, 0),
                     help="Revenue minus estimated API charges only. Not net profit.")
            b.metric("API costs as % of revenue", f"{result.api_cost_share_of_revenue:.1%}")
            st.caption(
                f"≈ {_usd(result.ai_cost_per_review, 4)} AI cost per review · "
                f"≈ {_usd(result.api_cost_per_restaurant, 2)} API cost per restaurant / month"
            )
        st.caption(
            "Note: Places API only exposes 5 reviews per business. A production product would use the "
            "owner-authorized Google Business Profile API to read all reviews and post approved replies, "
            "which changes the Google cost line."
        )

