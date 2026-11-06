"""Deterministic safety checks that run alongside the LLM.

The LLM is the primary classifier; these keyword rules are a safety net so a
serious complaint (food safety, harassment, discrimination, staff misconduct)
is never silently down-ranked, and so drafts that promise compensation or
invent contact details are flagged before a human approves them.

Kept in a separate module because the rules are policy, not prompting, and
need their own tests.
"""

from __future__ import annotations

import re

from models.schemas import ReviewAnalysis

# English patterns use word-boundary regexes; Arabic uses substring matching
# (Arabic words take attached prefixes such as ال / و / ب).
_SENSITIVE_EN: dict[str, list[str]] = {
    "food_safety": [
        r"food poison\w*", r"poison(ed|ing)", r"got sick", r"made (me|us|my \w+) sick",
        r"vomit\w*", r"threw up", r"diarrh\w*", r"cockroach\w*", r"roach(es)?", r"insect\w*",
        r"\bbugs?\b", r"\bworms?\b", r"\brats?\b", r"\bmice\b", r"\bmouse\b", r"mou?ld(y)?",
        r"hair in (my|the)", r"raw chicken", r"undercooked chicken", r"expired", r"rotten",
        r"\bspoiled\b", r"contaminat\w*", r"stomach (ache|pain|upset)", r"\bhospital\b", r"hospitali[sz]ed",
    ],
    "health_or_injury": [r"allergic reaction", r"(had|having|got) an? allerg\w*", r"anaphyla\w*", r"burned (me|my|him|her|his)", r"injur(ed|y|ies)", r"\bchoked?\b"],
    "harassment": [
        r"harass\w*", r"inappropriately touch\w*", r"touched me", r"\bcreepy\b", r"stalk\w*",
        r"sexual\w*", r"\bgroped?\b", r"followed me",
    ],
    "discrimination": [
        r"racis\w*", r"discriminat\w*", r"sexis\w*", r"because (i am|i'm) (a )?(woman|black|indian|"
        r"asian|arab|muslim|foreigner|disabled)", r"homophob\w*", r"xenophob\w*",
    ],
    "staff_misconduct": [
        r"\byell(ed|ing)? at\b", r"shout(ed|ing)? at", r"\bscream(ed|ing)? at", r"insult(ed|ing)",
        r"threaten\w*", r"\bswore\b", r"cursed at", r"pushed me", r"humiliat\w*", r"\bdrunk\b",
        r"aggressive", r"very rude", r"extremely rude", r"so rude",
    ],
    "legal_threat": [r"\blawyer\b", r"\bsue\b", r"legal action", r"report(ed)? (you )?to (the )?(ministry|municipality|police)"],
}

_SENSITIVE_AR: dict[str, list[str]] = {
    "food_safety": ["تسمم", "مسموم", "صرصور", "صراصير", "حشرة", "حشرات", "دودة", "فأر", "فئران",
                    "شعرة في", "شعر في", "منتهي الصلاحية", "منتهية الصلاحية", "متعفن", "عفن",
                    "فاسد", "نيء", "استفراغ", "تقيؤ", "إسهال", "اسهال", "المستشفى", "مستشفى"],
    "health_or_injury": ["حساسية", "حروق", "إصابة", "اصابة"],
    "harassment": ["تحرش", "مضايقة", "لمسني", "لمسها"],
    "discrimination": ["عنصري", "عنصرية", "تمييز"],
    "staff_misconduct": ["صرخ", "صراخ", "شتم", "سبّ", "إهانة", "اهانة", "أهان", "اهان", "تهديد",
                         "قليل الأدب", "وقح", "وقاحة"],
    "legal_threat": ["محامي", "البلدية", "وزارة التجارة", "الشرطة", "قضية"],
}

_COMPILED_EN = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in _SENSITIVE_EN.items()}

# Flags that always require the owner's personal attention at high urgency.
HIGH_URGENCY_FLAGS = {"food_safety", "harassment", "discrimination", "health_or_injury", "legal_threat"}
MEDIUM_URGENCY_FLAGS = {"staff_misconduct", "privacy"}

_URGENCY_ORDER = {"low": 0, "medium": 1, "high": 2}


def detect_sensitive_flags(text: str) -> set[str]:
    """Return sensitive categories found by keyword rules (English + Arabic)."""
    if not text:
        return set()
    found: set[str] = set()
    for flag, patterns in _COMPILED_EN.items():
        if any(p.search(text) for p in patterns):
            found.add(flag)
    for flag, words in _SENSITIVE_AR.items():
        if any(w in text for w in words):
            found.add(flag)
    return found


def _max_urgency(a: str, b: str) -> str:
    return a if _URGENCY_ORDER[a] >= _URGENCY_ORDER[b] else b


def apply_guardrails(analysis: ReviewAnalysis, review_text: str, rating: int | None) -> ReviewAnalysis:
    """Escalate (never de-escalate) the LLM's classification using deterministic rules."""
    keyword_flags = detect_sensitive_flags(review_text)
    flags = list(dict.fromkeys([*analysis.sensitive_flags, *sorted(keyword_flags)]))

    urgency = analysis.urgency
    needs_attention = analysis.needs_owner_attention
    reasons: list[str] = [analysis.attention_reason] if analysis.attention_reason else []

    if set(flags) & HIGH_URGENCY_FLAGS:
        urgency = "high"
        needs_attention = True
    elif set(flags) & MEDIUM_URGENCY_FLAGS:
        urgency = _max_urgency(urgency, "medium")
        needs_attention = True

    if rating is not None and rating <= 2:
        urgency = _max_urgency(urgency, "medium")
        needs_attention = True
        if not reasons:
            reasons.append(f"Low ({rating}-star) rating.")

    new_keyword_flags = keyword_flags - set(analysis.sensitive_flags)
    if new_keyword_flags:
        reasons.append(
            "Safety rule matched: " + ", ".join(sorted(f.replace("_", " ") for f in new_keyword_flags)) + "."
        )

    return analysis.model_copy(
        update={
            "sensitive_flags": flags,
            "urgency": urgency,
            "needs_owner_attention": needs_attention,
            "attention_reason": " ".join(reasons).strip(),
        }
    )


# --------------------------------------------------------------------------- #
# Reply checks (shown as warnings before approval)
# --------------------------------------------------------------------------- #

_COMMITMENT_EN = re.compile(
    r"\b(refund\w*|discount\w*|voucher\w*|coupon\w*|compensat\w*|free (meal|drink|coffee|dessert|item|order)|"
    r"on the house|complimentary|reimburs\w*|money back|\d+\s?% off)\b",
    re.IGNORECASE,
)
_COMMITMENT_AR = ["استرداد", "استرجاع المبلغ", "خصم", "مجان", "تعويض", "قسيمة", "كوبون", "على حسابنا"]

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")  # no trailing sentence period
_PHONE = re.compile(r"\+?\d[\d\s-]{6,}\d")
_PLACEHOLDER = re.compile(r"\[[^\]]{2,40}\]|\{[^}]{2,40}\}|<[^>]{2,40}>")


def check_reply(reply: str, approved_info: str) -> list[str]:
    """Return human-readable warnings about a draft reply."""
    warnings: list[str] = []
    info = (approved_info or "").lower()

    commitments = {m.group(0).lower() for m in _COMMITMENT_EN.finditer(reply)}
    commitments |= {w for w in _COMMITMENT_AR if w in reply}
    unapproved = [c for c in commitments if c.split()[0] not in info]
    if unapproved:
        warnings.append(
            "Mentions compensation (" + ", ".join(sorted(unapproved)) + ") that is not in your "
            "approved business information. Remove it or confirm it is authorized."
        )

    for pattern, label in ((_EMAIL, "email address"), (_PHONE, "phone number")):
        for match in pattern.findall(reply):
            value = match if isinstance(match, str) else match[0]
            if value.lower() not in info and value.replace(" ", "") not in info.replace(" ", ""):
                warnings.append(f"Contains an {label} ({value}) that is not in your approved information.")

    if _PLACEHOLDER.search(reply):
        warnings.append("Contains a placeholder such as [name] or {phone}. Fill it in before posting.")

    if len(reply.split()) > 180:
        warnings.append("Reply is long for a public Google review response (over 180 words).")

    return warnings
