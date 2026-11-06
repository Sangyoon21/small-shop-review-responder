"""SYNTHETIC demo data — NOT real Google reviews.

Used only when the user explicitly switches to Demo mode (e.g. no API keys, or
offline during a pitch). The business and every review below are fictional and
written by the project team. They are always labelled "synthetic" in the UI and
are never mixed with live Google results.

We deliberately do not store real Google reviews on disk: Google Maps Platform
terms restrict caching Places content.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from models.schemas import PlaceDetails, Review, ReviewAnalysis

DEMO_PLACE_ID = "demo-synthetic-cafe"
DEMO_PLACE_NAME = "Corniche Bean Café (Demo, Synthetic)"

_now = datetime.now(timezone.utc)


def _review(i: int, author: str, rating: int, text: str, lang: str, days_ago: int) -> Review:
    return Review(
        review_id=f"{DEMO_PLACE_ID}/reviews/{i}",
        place_id=DEMO_PLACE_ID,
        place_name=DEMO_PLACE_NAME,
        author_name=author,
        rating=rating,
        text=text,
        language=lang,
        publish_time=_now - timedelta(days=days_ago),
        relative_time=f"{days_ago} days ago",
        source="demo_synthetic",
    )


DEMO_REVIEWS: list[Review] = [
    _review(
        1, "Mariam K.", 5,
        "Best karak on the Corniche! The saffron cake was moist and not too sweet, and the "
        "barista (Rami) remembered my order on my second visit. Lovely sea view from the terrace "
        "in the evening.",
        "en", 3,
    ),
    _review(
        2, "Daniel P.", 3,
        "The shakshuka was genuinely delicious and portions are generous, but we waited almost "
        "25 minutes for food on a Friday morning and had to ask twice for water. Would come back "
        "on a quieter day.",
        "en", 9,
    ),
    _review(
        3, "Faisal A.", 1,
        "Found a hair in my chicken sandwich and when I told the cashier he just shrugged. I had a "
        "stomach ache the whole evening afterwards. Very disappointing for the price.",
        "en", 14,
    ),
    _review(
        4, "نورة", 5,
        "القهوة العربية ممتازة والتمر طازج، والجلسة الخارجية رائعة وقت المغرب. الموظفين محترمين "
        "وسريعين. أنصح فيه بقوة.",
        "ar", 20,
    ),
    _review(
        5, "خالد م.", 2,
        "المكان جميل لكن الموظف كان وقح معنا لما طلبنا تغيير الطاولة، وصرخ على زميله قدامنا. "
        "الأسعار مرتفعة مقارنة بالخدمة.",
        "ar", 31,
    ),
]

DEMO_PLACE = PlaceDetails(
    place_id=DEMO_PLACE_ID,
    name=DEMO_PLACE_NAME,
    address="Fictional address — Corniche, Doha, Qatar",
    rating=4.3,
    user_rating_count=812,
    google_maps_uri=None,
    primary_type="Café",
    editorial_summary="Fictional seaside café serving karak, Arabic coffee and breakfast plates.",
    reviews=DEMO_REVIEWS,
    source="demo_synthetic",
)

DEMO_BUSINESS_DESCRIPTION = (
    "Family-run café on the Doha Corniche serving karak, Arabic coffee, cakes and all-day breakfast."
)
DEMO_APPROVED_INFO = (
    "Contact for complaints: hello@cornichebean.example (owner reads daily).\n"
    "Open daily 7am-11pm. Friday mornings are our busiest time.\n"
    "Policy: if an order is wrong, we replace it free of charge when reported in-store.\n"
    "We do NOT offer refunds or discounts through public review replies."
)

# Pre-written sample outputs, used ONLY in Demo mode when no OpenAI key is set,
# so the UI can be shown offline. Always labelled "pre-written sample" in the UI.
DEMO_ANALYSES: dict[str, ReviewAnalysis] = {
    DEMO_REVIEWS[0].review_id: ReviewAnalysis(
        sentiment="positive", urgency="low", detected_language="en", suggested_response_language="en",
        key_complaints=[], complaint_categories=[],
        positive_feedback=["karak", "saffron cake not too sweet", "barista remembered order", "terrace sea view"],
        actionable_insights=["Feature the saffron cake in social posts", "Recognise Rami's regular-customer service"],
        sensitive_flags=[], needs_owner_attention=False, attention_reason="",
        suggested_response=(
            "Mariam, this made our day! We're so glad the saffron cake hit the right sweetness and "
            "that Rami remembered your order — he'll be thrilled to hear it. The terrace at sunset "
            "is our favourite spot too. See you for another karak soon! — The Corniche Bean team"
        ),
    ),
    DEMO_REVIEWS[1].review_id: ReviewAnalysis(
        sentiment="mixed", urgency="medium", detected_language="en", suggested_response_language="en",
        key_complaints=["25-minute wait for food on Friday morning", "had to ask twice for water"],
        complaint_categories=["service_speed"],
        positive_feedback=["delicious shakshuka", "generous portions"],
        actionable_insights=["Review Friday-morning kitchen staffing", "Serve water proactively at busy times"],
        sensitive_flags=[], needs_owner_attention=False, attention_reason="",
        suggested_response=(
            "Daniel, thank you for the kind words about the shakshuka and portions. You're right "
            "that a 25-minute wait and asking twice for water isn't the Friday experience we want — "
            "Friday mornings are our busiest time and we're looking at how we handle the rush. We'd "
            "love to welcome you back, busy day or quiet. — The Corniche Bean team"
        ),
    ),
    DEMO_REVIEWS[2].review_id: ReviewAnalysis(
        sentiment="negative", urgency="high", detected_language="en", suggested_response_language="en",
        key_complaints=["hair in chicken sandwich", "cashier shrugged when told", "stomach ache afterwards", "poor value"],
        complaint_categories=["food_safety", "staff_attitude", "price_value"],
        positive_feedback=[],
        actionable_insights=["Investigate hygiene procedures for that shift", "Retrain front-of-house on handling complaints"],
        sensitive_flags=["food_safety", "health_or_injury"], needs_owner_attention=True,
        attention_reason="Alleged foreign object in food and illness afterwards; owner should follow up personally.",
        suggested_response=(
            "Faisal, we're sorry to read this. What you describe is not acceptable to us, and the "
            "response at the counter should have been very different. We take food-safety concerns "
            "seriously and want to look into what happened. Please email us at "
            "hello@cornichebean.example so the owner can speak with you directly. — The Corniche Bean team"
        ),
    ),
    DEMO_REVIEWS[3].review_id: ReviewAnalysis(
        sentiment="positive", urgency="low", detected_language="ar", suggested_response_language="ar",
        key_complaints=[], complaint_categories=[],
        positive_feedback=["excellent Arabic coffee", "fresh dates", "outdoor seating at sunset", "respectful, fast staff"],
        actionable_insights=["Promote sunset outdoor seating"],
        sensitive_flags=[], needs_owner_attention=False, attention_reason="",
        suggested_response=(
            "أهلاً نورة، أسعدتنا كلماتك! يسعدنا أن القهوة العربية والتمر نالا إعجابك، وأن الجلسة الخارجية "
            "وقت المغرب كانت على ذوقك. سننقل شكرك للفريق، وننتظر زيارتك القادمة. — فريق كورنيش بين"
        ),
    ),
    DEMO_REVIEWS[4].review_id: ReviewAnalysis(
        sentiment="negative", urgency="medium", detected_language="ar", suggested_response_language="ar",
        key_complaints=["staff member rude when asked to change table", "staff shouted at colleague in front of guests", "prices high for the service"],
        complaint_categories=["staff_attitude", "price_value"],
        positive_feedback=["nice venue"],
        actionable_insights=["Speak with the team about conduct in front of guests", "Clarify table-change handling"],
        sensitive_flags=["staff_misconduct"], needs_owner_attention=True,
        attention_reason="Report of rude staff behavior and shouting in front of guests.",
        suggested_response=(
            "أخي خالد، نشكرك على صراحتك ونعتذر عن الطريقة التي عوملتم بها. ما وصفته لا يعكس الأسلوب الذي "
            "نريده لضيوفنا، وسنراجع الأمر مع الفريق. نرجو التواصل معنا عبر hello@cornichebean.example "
            "لنستمع إليك بشكل مباشر. — فريق كورنيش بين"
        ),
    ),
}



def demo_reply(review_id: str, language: str, tone: str = "friendly", current: str | None = None) -> str:
    """Pre-written reply for a demo review in the given language and tone.

    If `current` is one of the versions for this language/tone, the next version is
    returned, so "Regenerate" always shows a different reply.
    """
    from services.demo_replies import DEMO_REPLY_VARIANTS

    number = int(review_id.rsplit("/", 1)[-1])
    versions = DEMO_REPLY_VARIANTS[number][language][tone]
    if current in versions:
        return versions[(versions.index(current) + 1) % len(versions)]
    return versions[0]
