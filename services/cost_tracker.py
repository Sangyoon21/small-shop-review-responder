"""Track *actual* API usage and turn it into *estimated* costs.

Usage counts (tokens, request counts) are measured from real API responses.
Dollar amounts are estimates computed from configurable price assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from config import (
    DEFAULT_GOOGLE_PRICING,
    DEFAULT_MODEL_PRICING,
    GoogleSkuPricing,
    ModelPricing,
)


@dataclass
class OpenAICall:
    model: str
    purpose: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def openai_call_cost(call: OpenAICall, pricing: dict[str, ModelPricing]) -> float:
    price = pricing.get(call.model)
    if price is None:
        return 0.0
    cached = min(call.cached_input_tokens, call.input_tokens)
    uncached = call.input_tokens - cached
    return (
        uncached * price.input_per_million
        + cached * price.cached_input_per_million
        + call.output_tokens * price.output_per_million  # includes reasoning tokens
    ) / 1_000_000


def google_cost(request_count: int, sku: GoogleSkuPricing, apply_free_cap: bool = False) -> float:
    billable = max(0, request_count - sku.free_monthly_calls) if apply_free_cap else request_count
    return billable * sku.price_per_thousand / 1_000


@dataclass
class CostTracker:
    openai_calls: list[OpenAICall] = field(default_factory=list)
    google_requests: dict[str, int] = field(
        default_factory=lambda: {"text_search": 0, "place_details": 0}
    )
    failed_openai_requests: int = 0

    # --- recording -------------------------------------------------------- #
    def record_openai(
        self,
        model: str,
        purpose: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
        reasoning_tokens: int = 0,
    ) -> OpenAICall:
        call = OpenAICall(
            model=model,
            purpose=purpose,
            input_tokens=int(input_tokens or 0),
            output_tokens=int(output_tokens or 0),
            cached_input_tokens=int(cached_input_tokens or 0),
            reasoning_tokens=int(reasoning_tokens or 0),
        )
        self.openai_calls.append(call)
        return call

    def record_openai_failure(self) -> None:
        self.failed_openai_requests += 1

    def record_google(self, kind: str) -> None:
        self.google_requests[kind] = self.google_requests.get(kind, 0) + 1

    def reset(self) -> None:
        self.openai_calls.clear()
        self.google_requests = {"text_search": 0, "place_details": 0}
        self.failed_openai_requests = 0

    # --- aggregates ------------------------------------------------------- #
    @property
    def openai_request_count(self) -> int:
        return len(self.openai_calls)

    @property
    def input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.openai_calls)

    @property
    def output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.openai_calls)

    @property
    def reasoning_tokens(self) -> int:
        return sum(c.reasoning_tokens for c in self.openai_calls)

    @property
    def cached_input_tokens(self) -> int:
        return sum(c.cached_input_tokens for c in self.openai_calls)

    def openai_cost(self, pricing: dict[str, ModelPricing] | None = None) -> float:
        pricing = pricing or DEFAULT_MODEL_PRICING
        return sum(openai_call_cost(c, pricing) for c in self.openai_calls)

    def google_cost(
        self,
        pricing: dict[str, GoogleSkuPricing] | None = None,
        apply_free_cap: bool = False,
    ) -> float:
        pricing = pricing or DEFAULT_GOOGLE_PRICING
        return sum(
            google_cost(self.google_requests.get(kind, 0), sku, apply_free_cap)
            for kind, sku in pricing.items()
        )

    def total_cost(
        self,
        model_pricing: dict[str, ModelPricing] | None = None,
        google_pricing: dict[str, GoogleSkuPricing] | None = None,
        apply_free_cap: bool = False,
    ) -> float:
        return self.openai_cost(model_pricing) + self.google_cost(google_pricing, apply_free_cap)

    def per_model_breakdown(self, pricing: dict[str, ModelPricing] | None = None) -> list[dict]:
        pricing = pricing or DEFAULT_MODEL_PRICING
        rows: dict[str, dict] = {}
        for c in self.openai_calls:
            row = rows.setdefault(
                c.model,
                {"model": c.model, "requests": 0, "input_tokens": 0, "output_tokens": 0,
                 "reasoning_tokens": 0, "estimated_cost_usd": 0.0},
            )
            row["requests"] += 1
            row["input_tokens"] += c.input_tokens
            row["output_tokens"] += c.output_tokens
            row["reasoning_tokens"] += c.reasoning_tokens
            row["estimated_cost_usd"] += openai_call_cost(c, pricing)
        return list(rows.values())


# --------------------------------------------------------------------------- #
# Business simulation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SimulationInputs:
    restaurants: int
    reviews_per_restaurant: int
    subscription_price: float
    avg_input_tokens_per_review: int
    avg_output_tokens_per_review: int
    model_pricing: ModelPricing
    google_details_requests_per_restaurant: int = 30  # e.g. one review refresh per day
    google_details_price_per_thousand: float = 25.0
    google_free_monthly_calls: int = 0  # 0 = ignore Google's free cap (conservative)


@dataclass(frozen=True)
class SimulationResult:
    monthly_revenue: float
    monthly_ai_cost: float
    monthly_google_cost: float
    monthly_api_cost: float
    revenue_after_api_costs: float
    api_cost_share_of_revenue: float  # 0..1 (or >1 if API costs exceed revenue)
    ai_cost_per_review: float
    api_cost_per_restaurant: float


def simulate_monthly(inp: SimulationInputs) -> SimulationResult:
    reviews = inp.restaurants * inp.reviews_per_restaurant
    ai_cost_per_review = (
        inp.avg_input_tokens_per_review * inp.model_pricing.input_per_million
        + inp.avg_output_tokens_per_review * inp.model_pricing.output_per_million
    ) / 1_000_000
    ai_cost = reviews * ai_cost_per_review

    google_calls = inp.restaurants * inp.google_details_requests_per_restaurant
    billable_calls = max(0, google_calls - inp.google_free_monthly_calls)
    google_cost_total = billable_calls * inp.google_details_price_per_thousand / 1_000

    revenue = inp.restaurants * inp.subscription_price
    api_cost = ai_cost + google_cost_total
    return SimulationResult(
        monthly_revenue=revenue,
        monthly_ai_cost=ai_cost,
        monthly_google_cost=google_cost_total,
        monthly_api_cost=api_cost,
        revenue_after_api_costs=revenue - api_cost,
        api_cost_share_of_revenue=(api_cost / revenue) if revenue else 0.0,
        ai_cost_per_review=ai_cost_per_review,
        api_cost_per_restaurant=(api_cost / inp.restaurants) if inp.restaurants else 0.0,
    )
