"""Review card: shows one review, its AI analysis, and the human approval workflow."""

from __future__ import annotations

import html
from typing import Protocol

import streamlit as st

from models.schemas import Review
from services.safety import check_reply
from state import ReviewState

SENTIMENT_COLORS = {"positive": "green", "mixed": "orange", "negative": "red"}
URGENCY_COLORS = {"low": "gray", "medium": "orange", "high": "red"}
STATUS_LABELS = {
    "none": ("No reply yet", "gray"),
    "draft": ("Draft – awaiting approval", "blue"),
    "approved": ("Approved", "green"),
    "rejected": ("Rejected", "red"),
}


class ReviewActions(Protocol):
    def analyze(self, review: Review) -> None: ...
    def generate(self, review: Review, guidance: str = "", regenerate: bool = False) -> None: ...


def _stars(rating: int | None) -> str:
    if rating is None:
        return "No rating"
    return "★" * rating + "☆" * (5 - rating)


def _header_html(review: Review) -> str:
    name = html.escape(review.author_name)
    if review.author_uri:
        name = f'<a href="{html.escape(review.author_uri)}" target="_blank" rel="noopener">{name}</a>'
    photo = ""
    if review.author_photo_uri:
        photo = f'<img class="srr-avatar" src="{html.escape(review.author_photo_uri)}" alt="" referrerpolicy="no-referrer">'
    else:
        initial = html.escape((review.author_name or "?")[:1].upper())
        photo = f'<div class="srr-avatar srr-avatar-fallback">{initial}</div>'
    date = review.publish_time.strftime("%d %b %Y") if review.publish_time else ""
    rel = html.escape(review.relative_time or "")
    date_txt = f"{date} · {rel}" if date and rel else (date or rel)
    stars_cls = "srr-stars-low" if (review.rating or 5) <= 2 else "srr-stars"
    return (
        '<div class="srr-review-head">'
        f"{photo}"
        '<div class="srr-review-meta">'
        f'<div class="srr-author">{name}</div>'
        f'<div><span class="{stars_cls}">{_stars(review.rating)}</span>'
        f'<span class="srr-date">{html.escape(date_txt)}</span></div>'
        "</div></div>"
    )


def _review_body_html(review: Review) -> str:
    if not review.has_text:
        return '<div class="srr-review-text srr-muted">The reviewer left a star rating without written text.</div>'
    direction = ' dir="rtl"' if (review.language or "").startswith("ar") else ""
    return f'<div class="srr-review-text"{direction}>{html.escape(review.text)}</div>'


def _render_analysis(rs: ReviewState) -> None:
    a = rs.analysis
    if a is None:
        return
    badges = st.container(horizontal=True, gap="small")
    with badges:
        st.badge(f"Sentiment: {a.sentiment}", color=SENTIMENT_COLORS[a.sentiment])
        st.badge(f"Urgency: {a.urgency}", color=URGENCY_COLORS[a.urgency])
        if a.needs_owner_attention:
            st.badge("Owner attention", icon=":material/priority_high:", color="red")
        for flag in a.sensitive_flags:
            st.badge(flag.replace("_", " "), icon=":material/warning:", color="violet")
        if rs.analysis_origin == "sample":
            st.badge("Pre-written sample (offline demo)", color="gray")

    if a.needs_owner_attention and a.attention_reason:
        st.warning(a.attention_reason, icon=":material/flag:")

    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Key issues**")
        st.markdown("\n".join(f"- {html.escape(x)}" for x in a.key_complaints) or "_None mentioned_")
    with cols[1]:
        st.markdown("**What they liked**")
        st.markdown("\n".join(f"- {html.escape(x)}" for x in a.positive_feedback) or "_None mentioned_")
    with cols[2]:
        st.markdown("**Internal actions**")
        st.markdown("\n".join(f"- {html.escape(x)}" for x in a.actionable_insights) or "_None_")


def _render_reply(review: Review, rs: ReviewState, actions: ReviewActions, approved_info: str, ai_ready: bool) -> None:
    rid = review.review_id
    label, color = STATUS_LABELS[rs.status]
    head = st.container(horizontal=True, vertical_alignment="center")
    with head:
        st.markdown("**AI-generated reply**")
        st.badge(label, color=color)
        if rs.draft_origin == "sample":
            st.badge("Pre-written sample", color="gray")
        elif rs.draft_origin == "edited":
            st.badge("Edited by owner", color="blue")

    if not rs.draft:
        st.caption("No reply drafted yet.")
        if st.button("Generate reply", key=f"gen_{rid}", icon=":material/edit_note:", type="primary", disabled=not ai_ready):
            actions.generate(review)
        return

    # ---- Approved: locked, copyable ---------------------------------------- #
    if rs.status == "approved":
        st.success("Approved. Copy it and post it from your Google Business Profile.", icon=":material/check_circle:")
        st.code(rs.approved_text, language=None, wrap_lines=True)
        st.caption("Use the copy icon in the top-right of the box. Nothing is posted automatically.")
        c = st.container(horizontal=True)
        with c:
            if review.review_uri:
                st.link_button("Open review on Google Maps", review.review_uri, icon=":material/open_in_new:")
            if st.button("Unlock & edit", key=f"unlock_{rid}", icon=":material/lock_open:"):
                rs.status = "draft"
                st.rerun()
        return

    # ---- Edit mode -------------------------------------------------------- #
    edit_key = f"edit_{rid}"
    if rs.editing:
        st.text_area("Edit reply", key=edit_key, height=160, label_visibility="collapsed")
        c = st.container(horizontal=True)
        with c:
            if st.button("Save edits", key=f"save_{rid}", type="primary", icon=":material/save:"):
                new_text = st.session_state.get(edit_key, "").strip()
                if new_text and new_text != rs.draft:
                    rs.history.append(rs.draft)
                    rs.draft = new_text
                    rs.draft_origin = "edited"
                rs.editing = False
                rs.status = "draft"
                st.rerun()
            if st.button("Cancel", key=f"cancel_{rid}"):
                rs.editing = False
                st.rerun()
        return

    # ---- Draft view --------------------------------------------------------- #
    direction = ' dir="rtl"' if any("؀" <= ch <= "ۿ" for ch in rs.draft[:80]) else ""
    rejected_cls = " srr-reply-rejected" if rs.status == "rejected" else ""
    st.markdown(f'<div class="srr-reply{rejected_cls}"{direction}>{html.escape(rs.draft)}</div>', unsafe_allow_html=True)

    warnings = check_reply(rs.draft, approved_info)
    for w in warnings:
        st.warning(w, icon=":material/gpp_maybe:")

    buttons = st.container(horizontal=True, gap="small")
    with buttons:
        approve_label = "Approve anyway" if warnings else "Approve"
        if st.button(approve_label, key=f"approve_{rid}", type="primary", icon=":material/check:"):
            rs.status = "approved"
            rs.approved_text = rs.draft
            st.rerun()
        if st.button("Edit", key=f"editbtn_{rid}", icon=":material/edit:"):
            rs.editing = True
            st.session_state[edit_key] = rs.draft
            st.rerun()
        if st.button("Reject", key=f"reject_{rid}", icon=":material/close:", disabled=rs.status == "rejected"):
            rs.status = "rejected"
            st.rerun()

    with st.expander("Regenerate reply", icon=":material/refresh:", expanded=rs.status == "rejected"):
        guidance = st.text_input(
            "Optional guidance for the new version",
            key=f"guide_{rid}",
            placeholder="e.g. shorter, mention we're open late, warmer tone",
        )
        if st.button("Regenerate", key=f"regen_{rid}", icon=":material/autorenew:", disabled=not ai_ready):
            actions.generate(review, guidance=guidance, regenerate=True)
        if not ai_ready:
            st.caption("Regeneration needs an OPENAI_API_KEY.")
        if rs.history:
            st.caption(f"{len(rs.history)} earlier version(s) kept in this session.")


def render_review_card(
    review: Review,
    rs: ReviewState,
    actions: ReviewActions,
    approved_info: str,
    ai_ready: bool,
) -> None:
    with st.container(border=True):
        top = st.columns([5, 2], vertical_alignment="top")
        with top[0]:
            st.markdown(_header_html(review), unsafe_allow_html=True)
        with top[1]:
            if rs.analysis is None:
                if st.button(
                    "Analyze review", key=f"an_{review.review_id}", icon=":material/psychology:",
                    width="stretch", disabled=not ai_ready,
                ):
                    actions.analyze(review)
            else:
                if st.button(
                    "Re-analyze", key=f"rean_{review.review_id}", icon=":material/refresh:",
                    width="stretch", disabled=not ai_ready,
                ):
                    actions.analyze(review)

        st.markdown(_review_body_html(review), unsafe_allow_html=True)

        if review.translated_text:
            with st.expander(f"Google translation ({review.translated_language or 'translated'})"):
                st.write(review.translated_text)

        links = []
        if review.review_uri:
            links.append(f'<a href="{html.escape(review.review_uri)}" target="_blank" rel="noopener">View on Google Maps</a>')
        if review.flag_content_uri:
            links.append(f'<a href="{html.escape(review.flag_content_uri)}" target="_blank" rel="noopener">Report review</a>')
        if links:
            st.markdown('<div class="srr-links">' + " · ".join(links) + "</div>", unsafe_allow_html=True)

        if rs.error:
            st.error(rs.error, icon=":material/error:")
        if rs.notice:
            st.info(rs.notice, icon=":material/info:")
            rs.notice = None  # show once

        _render_analysis(rs)
        st.divider()
        _render_reply(review, rs, actions, approved_info, ai_ready)
