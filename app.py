"""Small Shop Review Responder — Streamlit entry point.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import config
from components.analytics import render_analytics, sample_stats
from components.costs import render_cost_section
from components.review_card import render_review_card
from models.schemas import PlaceDetails, Review
from services.ai_analyzer import (
    AIAnalyzerError,
    AIQuotaError,
    AINetworkError,
    BusinessContext,
    ReviewAI,
    reply_language,
)
from services.demo_data import (
    DEMO_ANALYSES,
    DEMO_APPROVED_INFO,
    DEMO_BUSINESS_DESCRIPTION,
    DEMO_PLACE,
    demo_reply,
)
from services.google_places import GooglePlacesClient, GooglePlacesError
from state import clear_place, init_state, review_state, tracker

LIVE = "Live Google Maps"
DEMO = "Demo (synthetic data)"

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=":material/reviews:",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root { --srr-brand: #8A1538; --srr-brand-soft: rgba(138, 21, 56, 0.08); }
.block-container { padding-top: 3.5rem; max-width: 1200px; }
.srr-hero { padding: 1.25rem 1.5rem; border-radius: 16px; margin-bottom: 1rem;
  background: linear-gradient(120deg, #8A1538 0%, #5E0E27 100%); color: #fff; }
.srr-hero h1 { color: #fff; font-size: 1.7rem; margin: 0 0 .25rem 0; padding: 0; }
.srr-hero p { margin: 0; opacity: .9; }
.srr-place h2 { margin-bottom: .1rem; padding-bottom: 0; }
.srr-place .srr-sub { opacity: .75; font-size: .95rem; }
.srr-place a { color: var(--srr-brand); font-weight: 600; text-decoration: none; margin-right: 1rem; }
.srr-section { font-size: .78rem; letter-spacing: .06em; text-transform: uppercase; opacity: .7;
  font-weight: 700; margin: .75rem 0 .25rem 0; }
.srr-review-head { display: flex; gap: .75rem; align-items: center; }
.srr-avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.srr-avatar-fallback { background: var(--srr-brand-soft); color: var(--srr-brand); display: flex;
  align-items: center; justify-content: center; font-weight: 700; }
.srr-author { font-weight: 600; }
.srr-author a { color: inherit; text-decoration: none; }
.srr-author a:hover { text-decoration: underline; }
.srr-stars { color: #E8A317; letter-spacing: 1px; }
.srr-stars-low { color: #B3261E; letter-spacing: 1px; }
.srr-date { opacity: .6; font-size: .85rem; margin-left: .5rem; }
.srr-review-text { margin: .75rem 0 .5rem 0; line-height: 1.55; white-space: pre-wrap; }
.srr-muted { opacity: .6; font-style: italic; }
.srr-links { font-size: .82rem; margin-bottom: .5rem; }
.srr-links a { color: var(--srr-brand); text-decoration: none; }
.srr-reply { background: var(--srr-brand-soft); border-left: 3px solid var(--srr-brand);
  padding: .8rem 1rem; border-radius: 8px; line-height: 1.55; white-space: pre-wrap; margin: .25rem 0 .75rem 0; }
.srr-reply[dir="rtl"] { border-left: none; border-right: 3px solid var(--srr-brand); }
.srr-reply-rejected { opacity: .55; text-decoration: line-through; }
.srr-attrib { font-family: Roboto, Arial, sans-serif; font-size: .85rem; opacity: .8; }
.srr-demo-banner { background: #FFF4D6; color: #6B4E00; border: 1px solid #F0D58C; border-radius: 10px;
  padding: .6rem 1rem; font-weight: 600; margin-bottom: .75rem; }
</style>
"""


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #


def _on_mode_change() -> None:
    """Switching data source never mixes demo data with live data."""
    clear_place()
    st.session_state["search_results"] = []
    if st.session_state["data_mode"] == DEMO:
        st.session_state["place"] = DEMO_PLACE.model_copy(deep=True)
        st.session_state["biz_description"] = DEMO_BUSINESS_DESCRIPTION
        st.session_state["biz_approved_info"] = DEMO_APPROVED_INFO
        st.session_state["biz_signature"] = "The Corniche Bean team"
    else:
        for k in ("biz_description", "biz_approved_info", "biz_signature"):
            st.session_state[k] = ""


def _apply_pending_prefill() -> None:
    pending = st.session_state.pop("_pending_prefill", None)
    if pending:
        for k, v in pending.items():
            st.session_state[k] = v


def sidebar(settings: config.Settings) -> dict:
    sb = st.sidebar
    sb.markdown(f"### :material/reviews: {config.APP_NAME}")
    sb.radio("Data source", [LIVE, DEMO], key="data_mode", on_change=_on_mode_change, horizontal=True)
    mode = st.session_state["data_mode"]

    # ---- 1. Search & select ------------------------------------------------- #
    if mode == LIVE:
        sb.markdown("**1 · Find a business**")
        if not settings.has_google_key:
            sb.error("GOOGLE_MAPS_API_KEY is missing. Add it to `.env` (see README), or use Demo mode.")
        with sb.form("search_form", border=False):
            query = st.text_input(
                "Restaurant name or area",
                placeholder="e.g. Flat White Qatar, cafés in The Pearl",
                label_visibility="collapsed",
            )
            bias = st.checkbox("Prefer results in Qatar", value=True)
            submitted = st.form_submit_button(
                "Search Google Maps", icon=":material/search:", type="primary",
                disabled=not settings.has_google_key, width="stretch",
            )
        if submitted:
            try:
                client = GooglePlacesClient(settings.google_maps_api_key, on_request=tracker().record_google)
                with sb:
                    with st.spinner("Searching Google Maps…"):
                        results = client.search_places(query, bias_to_qatar=bias)
                st.session_state["search_results"] = results
                if not results:
                    sb.warning("No businesses matched. Try adding a city, e.g. “… Doha”.")
            except GooglePlacesError as exc:
                sb.error(str(exc))

        results = st.session_state["search_results"]
        if results:
            ids = [p.place_id for p in results]
            labels = {p.place_id: f"{p.name} — {p.address.split(',')[0]}" for p in results}
            current: PlaceDetails | None = st.session_state["place"]
            default_idx = ids.index(current.place_id) if current and current.place_id in ids else 0
            chosen = sb.selectbox("Select a business", ids, index=default_idx, format_func=labels.get)
            is_loaded = current is not None and current.place_id == chosen
            if sb.button(
                "Refresh reviews" if is_loaded else "Load reviews",
                icon=":material/download:", width="stretch", type="secondary" if is_loaded else "primary",
            ):
                load_place(settings, chosen)
    else:
        sb.info("Demo mode uses a **fictional café with synthetic reviews**. No Google data is shown.",
                icon=":material/science:")

    # ---- 2. AI settings ------------------------------------------------------- #
    sb.divider()
    sb.markdown("**2 · AI reply settings**")
    model_options = list(config.DEFAULT_MODEL_PRICING)
    if settings.openai_model not in model_options:
        model_options.append(settings.openai_model)
    model = sb.selectbox(
        "Model", model_options, index=model_options.index(settings.openai_model),
        format_func=lambda m: config.DEFAULT_MODEL_PRICING[m].label if m in config.DEFAULT_MODEL_PRICING else m,
        key="model",
    )
    tone = sb.segmented_control(
        "Response tone", ["friendly", "professional", "formal"], default="friendly",
        format_func=lambda t: {"friendly": "Friendly & warm", "professional": "Professional", "formal": "Formal"}[t],
        key="tone", required=True,
    )
    language_mode = sb.selectbox(
        "Reply language", ["match", "en", "ar"],
        format_func={"match": "Arabic → Arabic, else English (default)", "en": "Always English", "ar": "Always Arabic"}.get,
        key="language_mode",
    )
    with sb.expander("Advanced"):
        effort = st.selectbox(
            "Reasoning effort", config.REASONING_EFFORT_OPTIONS,
            index=config.REASONING_EFFORT_OPTIONS.index(config.DEFAULT_REASONING_EFFORT),
            help="Higher effort can improve tricky replies but uses more (billed) output tokens.",
            key="effort",
        )

    # ---- 3. Business info --------------------------------------------------- #
    sb.divider()
    sb.markdown("**3 · Approved business information**")
    sb.caption("The AI may only state facts, policies and offers written here.")
    sb.text_area("Business description", key="biz_description", height=80,
                 placeholder="e.g. Family-run Lebanese bakery in Al Sadd, open since 2015.")
    sb.text_area("Policies & contact info", key="biz_approved_info", height=120,
                 placeholder="e.g. Contact: feedback@yourcafe.qa\nWrong orders are replaced free of charge.\nWe don't offer refunds via review replies.")
    sb.text_input("Reply signature", key="biz_signature", placeholder="e.g. Sara, Owner")

    # ---- 4. Usage & pricing ------------------------------------------------- #
    sb.divider()
    sb.markdown("**4 · API usage (this session)**")
    model_pricing, google_pricing = _pricing_inputs(sb, model)
    t = tracker()
    u1, u2 = sb.columns(2)
    u1.metric("AI requests", t.openai_request_count)
    u2.metric("Tokens", f"{t.input_tokens + t.output_tokens:,}")
    u1.metric("Google requests", sum(t.google_requests.values()))
    u2.metric("Est. cost", f"${t.total_cost(model_pricing, google_pricing):.4f}",
              help="Estimate from configurable prices; Google list price before free caps.")

    sb.divider()
    sb.caption(
        ("Google key: configured ✓" if settings.has_google_key else "Google key: missing ✗")
        + "  ·  "
        + ("OpenAI key: configured ✓" if settings.has_openai_key else "OpenAI key: missing ✗")
    )
    if sb.button("Clear session data", icon=":material/delete_sweep:"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    return {
        "mode": mode,
        "model": model,
        "tone": tone or "friendly",
        "language_mode": language_mode,
        "effort": effort,
        "model_pricing": model_pricing,
        "google_pricing": google_pricing,
    }


def _pricing_inputs(sb, selected_model: str):
    model_pricing = dict(config.DEFAULT_MODEL_PRICING)
    if selected_model not in model_pricing:
        base = config.DEFAULT_MODEL_PRICING[config.DEFAULT_MODEL]
        model_pricing[selected_model] = config.ModelPricing(selected_model, base.input_per_million,
                                                            base.output_per_million, base.cached_input_per_million)
    google_pricing = dict(config.DEFAULT_GOOGLE_PRICING)
    with sb.expander("Edit price assumptions"):
        st.caption("USD. Verify against official pricing pages.")
        for key, p in list(model_pricing.items()):
            st.markdown(f"**{p.label}** (per 1M tokens)")
            c1, c2, c3 = st.columns(3)
            inp = c1.number_input("Input", 0.0, 1000.0, p.input_per_million, 0.05, key=f"p_in_{key}")
            cached = c2.number_input("Cached", 0.0, 1000.0, p.cached_input_per_million, 0.01, key=f"p_ca_{key}")
            out = c3.number_input("Output", 0.0, 1000.0, p.output_per_million, 0.05, key=f"p_out_{key}")
            model_pricing[key] = config.ModelPricing(p.label, inp, out, cached)
        for key, s in list(google_pricing.items()):
            price = st.number_input(f"{s.sku} (per 1,000)", 0.0, 1000.0, s.price_per_thousand, 0.5, key=f"g_{key}")
            google_pricing[key] = config.GoogleSkuPricing(s.sku, price, s.free_monthly_calls)
    return model_pricing, google_pricing


# --------------------------------------------------------------------------- #
# Actions
# --------------------------------------------------------------------------- #


def load_place(settings: config.Settings, place_id: str) -> None:
    try:
        client = GooglePlacesClient(settings.google_maps_api_key, on_request=tracker().record_google)
        with st.spinner("Fetching public reviews from Google Maps…"):
            details = client.get_place_details(place_id)
    except GooglePlacesError as exc:
        st.session_state["flash"] = ("error", str(exc))
        st.rerun()
        return
    previous: PlaceDetails | None = st.session_state["place"]
    if previous is None or previous.place_id != details.place_id:
        clear_place()
        st.session_state["_pending_prefill"] = {
            "biz_description": details.editorial_summary or "",
            "biz_approved_info": "",
            "biz_signature": "",
        }
    st.session_state["place"] = details
    st.session_state["flash"] = (
        "success",
        f"Retrieved {len(details.reviews)} public review(s) from Google for {details.name}.",
    )
    st.rerun()


class Actions:
    """Implements ReviewActions for review cards; all results go to session state."""

    def __init__(self, settings: config.Settings, opts: dict, ctx: BusinessContext):
        self.settings = settings
        self.opts = opts
        self.ctx = ctx

    def _use_sample(self, review: Review) -> bool:
        return review.source == "demo_synthetic" and not self.settings.has_openai_key

    def _ai(self) -> ReviewAI:
        return ReviewAI(
            api_key=self.settings.openai_api_key,
            model=self.opts["model"],
            reasoning_effort=self.opts["effort"],
            tracker=tracker(),
        )

    def _analyze_one(self, review: Review) -> None:
        rs = review_state(review.review_id)
        rs.error = None
        if self._use_sample(review):
            language = reply_language(review, self.ctx.language_mode)
            analysis = DEMO_ANALYSES[review.review_id].model_copy(update={
                "suggested_response": demo_reply(review.review_id, language, self.ctx.tone),
                "suggested_response_language": language,
            })
            origin = "sample"
        else:
            analysis, origin = self._ai().analyze(review, self.ctx), "live"
        rs.analysis, rs.analysis_origin = analysis, origin
        unedited_sample = rs.draft_origin == "sample" and rs.status == "draft"
        if (not rs.draft or unedited_sample) and analysis.suggested_response.strip():
            rs.draft, rs.draft_origin, rs.status = analysis.suggested_response.strip(), origin, "draft"

    def analyze(self, review: Review) -> None:
        rs = review_state(review.review_id)
        try:
            with st.spinner("Analyzing review…"):
                self._analyze_one(review)
        except AIAnalyzerError as exc:
            rs.error = str(exc)
        st.rerun()

    def analyze_many(self, reviews: list[Review]) -> None:
        todo = [r for r in reviews if review_state(r.review_id).analysis is None]
        if not todo:
            st.session_state["flash"] = ("info", "All reviews are already analyzed.")
            st.rerun()
        bar = st.progress(0.0, text="Analyzing reviews…")
        for i, review in enumerate(todo, 1):
            try:
                self._analyze_one(review)
            except (AIQuotaError, AINetworkError) as exc:
                st.session_state["flash"] = ("error", f"Stopped: {exc}")
                break
            except AIAnalyzerError as exc:
                review_state(review.review_id).error = str(exc)
                if "API key" in str(exc):
                    st.session_state["flash"] = ("error", str(exc))
                    break
            bar.progress(i / len(todo), text=f"Analyzed {i} of {len(todo)}")
        st.rerun()

    def generate(self, review: Review, guidance: str = "", regenerate: bool = False) -> None:
        rs = review_state(review.review_id)
        rs.error = None
        if self._use_sample(review):
            language = reply_language(review, self.ctx.language_mode)
            sample = demo_reply(review.review_id, language, self.ctx.tone,
                                current=rs.draft if regenerate else None)
            if rs.draft and rs.draft != sample:
                rs.history.append(rs.draft)
            rs.draft, rs.draft_origin, rs.status, rs.editing = sample, "sample", "draft", False
            if regenerate and guidance.strip():
                rs.notice = "Offline demo: showing another pre-written version. Custom guidance needs a live AI key."
            st.rerun()
        previous = [*rs.history, rs.draft] if (regenerate and rs.draft) else None
        try:
            with st.spinner("Writing a new reply…" if regenerate else "Writing reply…"):
                draft = self._ai().generate_reply(review, self.ctx, rs.analysis, previous, guidance)
        except AIAnalyzerError as exc:
            rs.error = str(exc)
            st.rerun()
        if rs.draft:
            rs.history.append(rs.draft)
        rs.draft, rs.draft_origin, rs.status, rs.editing = draft.reply.strip(), "live", "draft", False
        st.rerun()


# --------------------------------------------------------------------------- #
# Main area
# --------------------------------------------------------------------------- #


def hero() -> None:
    st.markdown(
        '<div class="srr-hero"><h1>Small Shop Review Responder</h1>'
        "<p>Understand your Google reviews and reply to every customer personally, with AI drafts "
        "you approve before anything goes public.</p></div>",
        unsafe_allow_html=True,
    )


def show_flash() -> None:
    flash = st.session_state.pop("flash", None)
    if flash:
        kind, msg = flash
        getattr(st, kind)(msg)


def welcome(settings: config.Settings, mode: str) -> None:
    results = st.session_state["search_results"]
    if results:
        st.markdown("#### Search results")
        st.caption("Pick a business in the sidebar and click **Load reviews**.")
        df = pd.DataFrame(
            [{"Business": p.name, "Address": p.address, "Google rating": p.rating,
              "Ratings": p.user_rating_count, "Type": p.primary_type, "Google Maps": p.google_maps_uri}
             for p in results]
        )
        st.dataframe(
            df, hide_index=True, width="stretch",
            column_config={
                "Google rating": st.column_config.NumberColumn(format="%.1f ⭐"),
                "Ratings": st.column_config.NumberColumn(format="%d"),
                "Google Maps": st.column_config.LinkColumn(display_text="Open ↗"),
            },
        )
        st.markdown('<div class="srr-attrib">Results from Google Maps</div>', unsafe_allow_html=True)
        return

    cols = st.columns(3)
    steps = [
        (":material/search:", "Find your business", "Search Google Maps by name or area, e.g. *Flat White Qatar*."),
        (":material/psychology:", "Analyze reviews", "Sentiment, urgency, key issues and safety flags, in English or Arabic."),
        (":material/verified:", "Approve replies", "Edit, approve and copy personalised replies. Nothing is posted automatically."),
    ]
    for col, (icon, title, body) in zip(cols, steps):
        with col.container(border=True):
            st.markdown(f"### {icon}\n**{title}**\n\n{body}")
    if mode == LIVE and not settings.has_google_key:
        st.warning("Live mode needs `GOOGLE_MAPS_API_KEY`. Switch to **Demo** in the sidebar to explore with synthetic data.")
    if not settings.has_openai_key:
        st.info("`OPENAI_API_KEY` is not set: AI analysis is disabled for live reviews.")


def place_header(place: PlaceDetails) -> None:
    if place.source == "demo_synthetic":
        st.markdown(
            '<div class="srr-demo-banner">⚠ DEMO MODE: fictional business and synthetic reviews. '
            "This is not real Google data.</div>",
            unsafe_allow_html=True,
        )
    links = []
    if place.google_maps_uri:
        links.append(f'<a href="{html.escape(place.google_maps_uri)}" target="_blank" rel="noopener">Google Maps ↗</a>')
    if place.website_uri:
        links.append(f'<a href="{html.escape(place.website_uri)}" target="_blank" rel="noopener">Website ↗</a>')
    sub = " · ".join(x for x in [place.primary_type, place.address] if x)
    st.markdown(
        f'<div class="srr-place"><h2>{html.escape(place.name)}</h2>'
        f'<div class="srr-sub">{html.escape(sub)}</div><div>{"".join(links)}</div></div>',
        unsafe_allow_html=True,
    )


def metrics(place: PlaceDetails) -> None:
    stats = sample_stats(place, st.session_state["review_states"])
    left, right = st.columns([2, 4], gap="medium")
    with left:
        st.markdown('<div class="srr-section">Google overall · all customers</div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        a.metric("Overall rating", f"{place.rating:.1f} ★" if place.rating is not None else "—", border=True)
        b.metric("Total ratings", f"{place.user_rating_count:,}" if place.user_rating_count is not None else "—", border=True)
    with right:
        st.markdown('<div class="srr-section">Retrieved sample · Places API (max 5)</div>', unsafe_allow_html=True)
        c = st.columns(4)
        analyzed_note = f"{stats['analyzed']}/{stats['retrieved']} analyzed"
        c[0].metric("Retrieved", stats["retrieved"], border=True,
                    help="Google's Places API returns at most 5 reviews per business, selected by Google.")
        c[1].metric("Positive", stats["positive"], border=True, help=f"AI sentiment · {analyzed_note}")
        c[2].metric("Negative", stats["negative"], border=True,
                    help=f"AI sentiment · {analyzed_note}. Mixed: {stats['mixed']}. 1–2★ reviews: {stats['low_star']}.")
        c[3].metric("Need attention", stats["attention"], border=True, help=f"Flagged by AI + safety rules · {analyzed_note}")
    if place.source == "google_places":
        st.markdown(
            f'<div class="srr-attrib">Reviews and ratings from Google Maps. Sample shows {stats["retrieved"]} of '
            f'{place.user_rating_count or "?"} ratings, as returned by Google.</div>',
            unsafe_allow_html=True,
        )


def _priority(review: Review) -> tuple:
    a = review_state(review.review_id).analysis
    urgency = {"high": 0, "medium": 1, "low": 2}[a.urgency] if a else 3
    return (0 if a and a.needs_owner_attention else 1, urgency, review.rating or 0)


def reviews_tab(place: PlaceDetails, actions: Actions, ai_ready: bool, approved_info: str) -> None:
    if not place.reviews:
        st.info(
            "Google returned no public reviews for this business. The Places API only exposes up to 5 "
            "reviews, and some businesses have none available.",
            icon=":material/inbox:",
        )
        return

    bar = st.container(horizontal=True, vertical_alignment="bottom")
    with bar:
        if st.button("Analyze all reviews", type="primary", icon=":material/auto_awesome:", disabled=not ai_ready):
            actions.analyze_many(place.reviews)
        flt = st.segmented_control(
            "Show", ["All", "Needs attention", "Negative", "Awaiting approval", "Approved"],
            default="All", key="review_filter", label_visibility="collapsed",
        ) or "All"
        priority_first = st.toggle("Priority first", value=True)

    if not ai_ready:
        st.info("AI features need `OPENAI_API_KEY` in `.env`. You can still read the reviews.", icon=":material/key:")

    reviews = sorted(place.reviews, key=_priority) if priority_first else list(place.reviews)

    def keep(r: Review) -> bool:
        rs = review_state(r.review_id)
        a = rs.analysis
        return {
            "All": True,
            "Needs attention": bool(a and a.needs_owner_attention),
            "Negative": bool(a and a.sentiment == "negative") or (r.rating is not None and r.rating <= 2),
            "Awaiting approval": rs.status == "draft",
            "Approved": rs.status == "approved",
        }[flt]

    shown = [r for r in reviews if keep(r)]
    if not shown:
        st.caption("No reviews match this filter.")
    for review in shown:
        render_review_card(review, review_state(review.review_id), actions, approved_info, ai_ready)

    if place.source == "google_places":
        st.markdown('<div class="srr-attrib">Reviews from Google Maps. Review content © its authors.</div>',
                    unsafe_allow_html=True)


def main() -> None:
    init_state()
    settings = config.get_settings()
    if "_first_run_done" not in st.session_state:
        st.session_state["_first_run_done"] = True
        # Shared/public links have no keys: open straight into the working demo.
        if not settings.has_google_key:
            st.session_state["data_mode"] = DEMO
            _on_mode_change()
    _apply_pending_prefill()
    st.markdown(CSS, unsafe_allow_html=True)
    opts = sidebar(settings)

    hero()
    show_flash()

    place: PlaceDetails | None = st.session_state["place"]
    if place is None:
        welcome(settings, opts["mode"])
        return

    ctx = BusinessContext(
        name=place.name.replace(" (Demo, Synthetic)", ""),
        description=st.session_state.get("biz_description", ""),
        approved_info=st.session_state.get("biz_approved_info", ""),
        signature=st.session_state.get("biz_signature", ""),
        tone=opts["tone"],
        language_mode=opts["language_mode"],
    )
    ai_ready = settings.has_openai_key or place.source == "demo_synthetic"
    actions = Actions(settings, opts, ctx)

    place_header(place)
    metrics(place)
    st.write("")

    tab_reviews, tab_analytics, tab_costs = st.tabs(
        [":material/rate_review: Reviews", ":material/insights: Analytics", ":material/payments: Costs & financials"]
    )
    with tab_reviews:
        reviews_tab(place, actions, ai_ready, ctx.approved_info)
    with tab_analytics:
        render_analytics(place, st.session_state["review_states"])
    with tab_costs:
        render_cost_section(tracker(), opts["model_pricing"], opts["google_pricing"], opts["model"])

    if st.session_state["search_results"] and opts["mode"] == LIVE:
        with st.expander("Search results"):
            welcome(settings, opts["mode"])


main()
