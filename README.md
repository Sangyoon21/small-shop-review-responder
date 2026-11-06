# Small Shop Review Responder

An AI-assisted review manager for small restaurants, cafés and shops in Qatar. It pulls **real public Google Maps reviews** through the official Google Places API (New), analyzes each one with OpenAI GPT-5.4 (sentiment, urgency, key issues, safety flags), and drafts personalised replies in the review's language (English or Arabic). **A person approves every reply. Nothing is posted automatically.**

> **Important limitation:** the Google Places API returns **at most 5 reviews per business**, chosen by Google. The app never claims to retrieve all reviews and never fills gaps with invented ones. Sample statistics are always labelled as such and kept separate from the business's overall Google rating.

---

## Features

| Area | What it does |
|---|---|
| Search | Google Places **Text Search (New)** with a Qatar location bias. Shows name, address, rating, rating count and a Google Maps link. |
| Reviews | **Place Details (New)**: up to 5 public reviews with reviewer name and profile link, stars, date, original-language text (plus Google's translation if different) and a link to the review on Maps. |
| AI analysis | Sentiment, urgency, key complaints, positive feedback, internal action items, sensitive flags (food safety, harassment, discrimination, staff misconduct, health or injury, legal threats) and a draft reply. Output is validated with **Pydantic** against a **strict JSON schema**. |
| Safety net | Keyword rules (English and Arabic) can raise the AI's urgency but never lower it. Draft replies are checked for unapproved refunds or discounts, invented phone numbers or emails, placeholders and excessive length. |
| Replies | Three tones (friendly and warm, professional, formal). By default, Arabic reviews get Arabic replies and all other reviews get English replies. You can regenerate with optional guidance ("shorter", "mention we open late"), edit, approve, reject, and copy approved replies. |
| Dashboard | Overall Google metrics shown separately from retrieved-sample metrics. Charts for star distribution, sentiment, complaint themes and high-priority reviews. |
| Costs | Measured OpenAI tokens and requests, Google request counts, editable price assumptions, estimated costs, and a monthly business simulation. |
| Demo mode | A clearly labelled **synthetic** café with pre-written sample outputs, so the UI can be shown offline. It is never mixed with live data. |

---

## Quick start

```bash
cd small-shop-review-responder
python3.11 -m venv .venv && source .venv/bin/activate   # Python 3.11+
pip install -r requirements.txt
cp .env.example .env        # then add your keys (see below)
streamlit run app.py
```

The app opens at http://localhost:8501. Without keys it opens in **Demo (synthetic data)** mode automatically.

**To share a public demo link** (free, via Streamlit Community Cloud), see [DEPLOY.md](DEPLOY.md).

---

## Setup in detail

### 1. Create a Google Cloud project
1. Go to <https://console.cloud.google.com/>, then **Select a project → New project**.
2. Name it (e.g. `review-responder`) and click **Create**.

### 2. Enable Places API (New)
1. **APIs & Services → Library**, then search for **"Places API (New)"**. It is *not* the legacy "Places API".
2. Click **Enable**.

### 3. Enable billing
Google Maps Platform requires a billing account even for free-tier usage.
**Billing → Link a billing account** (or create one). Then set up a **budget alert** under **Billing → Budgets & alerts**; $10 is a sensible limit for a demo.

### 4. Create and secure a Google Maps API key
1. **APIs & Services → Credentials → Create credentials → API key.**
2. Click the key, then **API restrictions → Restrict key** and select only **Places API (New)**.
3. **Application restrictions**: for a laptop demo choose *None* or *IP addresses* (your current IP). Do **not** use *HTTP referrers*: this app calls Google from the Python server, not from the browser.
4. Optional: under **APIs & Services → Places API (New) → Quotas**, lower the per-day request quota (e.g. 200) to cap spending.

### 5. Create an OpenAI API key
1. Go to <https://platform.openai.com/api-keys>, then **Create new secret key**.
2. Make sure the project has credits under **Settings → Billing**, and that it can use `gpt-5.4` / `gpt-5.4-mini`.
3. Optional: set a monthly usage limit.

### 6. Configure `.env`
```dotenv
GOOGLE_MAPS_API_KEY=AIza...
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4        # or gpt-5.4-mini
```
`.env` is in `.gitignore`. Never commit it. Keys are read only on the server and never shown in the UI; the sidebar only says "configured ✓" or "missing ✗".

### 7. Install dependencies
```bash
pip install -r requirements.txt
```

### 8. Run the app
```bash
streamlit run app.py
```

### 9. Test with real restaurants in Qatar
1. Keep **Live Google Maps** selected in the sidebar.
2. Search, for example, `Flat White Qatar`, `Starbucks Doha`, `Coffee shops in The Pearl Qatar` or `Restaurants in Lusail`.
3. Pick a result, then click **Load reviews**. A green banner confirms how many reviews Google actually returned.
4. Add your **approved business information** in the sidebar: a contact email and real policies. The AI may only state what is written there.
5. Click **Analyze all reviews**, or analyze reviews one at a time.
6. Review each draft, then **Edit**, **Regenerate** (with optional guidance), **Approve** or **Reject** it.
7. Copy approved replies (copy icon on the code box) and post them yourself from **Google Business Profile**.

### 10. Run the tests
```bash
pytest -q
```
All tests use mocked Google and OpenAI responses, so they cost nothing.

---

## Understanding API costs

**Measured vs. estimated.** Token counts, request counts and Google call counts are measured from real API responses in your session. Dollar amounts are estimates computed from the configurable prices in **Sidebar → API usage → Edit price assumptions**.

### OpenAI (per 1M tokens, checked 2026-11-06)
| Model | Input | Cached input | Output |
|---|---|---|---|
| GPT-5.4 (default) | $2.50 | $0.25 | $15.00 |
| GPT-5.4 mini | $0.75 | $0.075 | $4.50 |

Reasoning tokens are billed as output tokens. The app uses `reasoning.effort = "low"` by default; change it under **Advanced**. These prices match the project brief and third-party trackers, but I couldn't load OpenAI's official pricing page directly. **Verify them at the OpenAI pricing page before you rely on them.**

### Google Places API (New) (per 1,000 requests, 0–100k tier, checked 2026-11-06)
Google bills each request at the SKU of the **most expensive field** in the field mask.

| Call | Fields that set the SKU | SKU | Price | Free / month |
|---|---|---|---|---|
| Text Search | `rating`, `userRatingCount` | Text Search Enterprise | $35.00 | 1,000 |
| Place Details | `reviews`, `editorialSummary` | Place Details Enterprise + Atmosphere | $25.00 | 1,000 |

Source: <https://developers.google.com/maps/billing-and-pricing/pricing>. Free caps apply per SKU per billing account. The in-app estimate shows the **list price before free caps** (conservative). Your actual demo bill will likely be $0 while you stay under the caps.

**Typical demo cost:** 5 searches + 5 place loads + 25 analyses (~1.5k input / ~0.7k output tokens each) comes to roughly **$0.30 in list-price Google fees** (likely $0 within the free caps) plus **about $0.35 in GPT-5.4 tokens**. These figures are estimates; check the in-app cost tab for your measured usage.

### Business simulation
The **Costs & financials** tab models monthly subscription revenue against API costs. Its result is labelled **"Revenue after API costs", not profit**, because salaries, hosting, marketing, payment fees and taxes are excluded.

---

## Limitations and compliance notes

- **5 reviews maximum** per business from the Places API, chosen by Google (not necessarily the newest). To read every review and post replies programmatically, a production version should use the owner-authorized **Google Business Profile API**, which requires the owner's OAuth consent and Google approval.
- **No auto-posting.** The app produces approved text for a person to post.
- **Attribution.** Reviewer names link to their Google profiles, each review links to Google Maps, and "Google Maps" attribution is shown with all Places content.
- **Caching.** Google content is kept only in the in-memory Streamlit session. Nothing from Google is written to disk. Use **Clear session data** to discard it. Google Maps Platform terms restrict caching Places content.
- **Untrusted input.** Review text is wrapped in tagged blocks and treated as data. Attempts to inject instructions are neutralized and covered by tests. As with any LLM, a person must still review every reply.
- **The keyword safety net is a heuristic.** It catches common English and Gulf Arabic phrasing but won't catch everything. The AI classification is primary.
- **Arabic quality.** Replies to Arabic reviews are in Modern Standard Arabic. Have a native speaker spot-check them before the pitch.
- **Pricing changes.** All prices are editable assumptions. Re-verify them before quoting numbers to investors.
- **No fabricated fallback.** If a live request fails, the app shows the error. Demo data appears only when you switch to Demo mode, and it is labelled synthetic everywhere.

---

## Project structure

```
small-shop-review-responder/
├── app.py                  # Streamlit UI: sidebar, dashboard, actions
├── config.py               # env vars, model + Google pricing assumptions
├── state.py                # session-state model (drafts survive reruns)
├── services/
│   ├── google_places.py    # Places API (New) client + parsing + errors
│   ├── ai_analyzer.py      # OpenAI Responses API, prompts, validation
│   ├── safety.py           # deterministic guardrails + reply checks
│   ├── cost_tracker.py     # usage tracking, cost estimates, simulation
│   └── demo_data.py        # SYNTHETIC demo café (clearly labelled)
├── models/schemas.py       # Pydantic models + strict JSON schema helper
├── components/
│   ├── review_card.py      # review card + approval workflow
│   ├── analytics.py        # sample charts
│   └── costs.py            # usage + financial simulation panel
├── tests/                  # pytest, all API calls mocked
├── .streamlit/config.toml  # theme
├── requirements.txt
├── .env.example
└── .gitignore
```

`safety.py`, `demo_data.py`, `state.py` and `components/costs.py` were added beyond the suggested layout. Each keeps one concern (policy rules, synthetic data, UI state, cost UI) out of the larger modules and makes it testable on its own.
