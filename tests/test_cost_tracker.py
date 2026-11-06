"""Cost calculation and simulation tests."""

import pytest

from config import DEFAULT_GOOGLE_PRICING, DEFAULT_MODEL_PRICING, GoogleSkuPricing, ModelPricing
from services.cost_tracker import (
    CostTracker,
    OpenAICall,
    SimulationInputs,
    google_cost,
    openai_call_cost,
    simulate_monthly,
)


def test_default_prices_match_reference_values():
    assert DEFAULT_MODEL_PRICING["gpt-5.4"].input_per_million == 2.50
    assert DEFAULT_MODEL_PRICING["gpt-5.4"].output_per_million == 15.00
    assert DEFAULT_MODEL_PRICING["gpt-5.4-mini"].input_per_million == 0.75
    assert DEFAULT_MODEL_PRICING["gpt-5.4-mini"].output_per_million == 4.50


def test_openai_call_cost_math():
    call = OpenAICall(model="gpt-5.4", purpose="analysis", input_tokens=1_000_000, output_tokens=1_000_000)
    assert openai_call_cost(call, DEFAULT_MODEL_PRICING) == pytest.approx(17.50)

    mini = OpenAICall(model="gpt-5.4-mini", purpose="reply", input_tokens=2_000, output_tokens=500)
    assert openai_call_cost(mini, DEFAULT_MODEL_PRICING) == pytest.approx((2_000 * 0.75 + 500 * 4.50) / 1e6)


def test_cached_tokens_use_cached_rate():
    call = OpenAICall(model="gpt-5.4", purpose="x", input_tokens=1_000, output_tokens=0, cached_input_tokens=400)
    expected = (600 * 2.50 + 400 * 0.25) / 1e6
    assert openai_call_cost(call, DEFAULT_MODEL_PRICING) == pytest.approx(expected)


def test_unknown_model_costs_zero_rather_than_crashing():
    call = OpenAICall(model="mystery", purpose="x", input_tokens=10, output_tokens=10)
    assert openai_call_cost(call, DEFAULT_MODEL_PRICING) == 0.0


def test_tracker_aggregates_and_custom_pricing():
    t = CostTracker()
    t.record_openai("gpt-5.4", "analysis", 1_000, 500, reasoning_tokens=200)
    t.record_openai("gpt-5.4", "reply", 800, 300)
    t.record_openai("gpt-5.4-mini", "reply", 1_000, 1_000)
    assert t.openai_request_count == 3
    assert t.input_tokens == 2_800 and t.output_tokens == 1_800 and t.reasoning_tokens == 200

    expected = (1_800 * 2.5 + 800 * 15 + 1_000 * 0.75 + 1_000 * 4.5) / 1e6
    assert t.openai_cost() == pytest.approx(expected)

    custom = {**DEFAULT_MODEL_PRICING, "gpt-5.4": ModelPricing("x", 0, 0, 0)}
    assert t.openai_cost(custom) == pytest.approx((1_000 * 0.75 + 1_000 * 4.5) / 1e6)

    rows = {r["model"]: r for r in t.per_model_breakdown()}
    assert rows["gpt-5.4"]["requests"] == 2
    assert rows["gpt-5.4-mini"]["input_tokens"] == 1_000


def test_google_cost_and_free_cap():
    sku = GoogleSkuPricing("Details", 25.0, 1_000)
    assert google_cost(4, sku) == pytest.approx(0.10)
    assert google_cost(4, sku, apply_free_cap=True) == 0.0
    assert google_cost(1_500, sku, apply_free_cap=True) == pytest.approx(12.5)

    t = CostTracker()
    t.record_google("text_search")
    t.record_google("place_details")
    t.record_google("place_details")
    expected = (1 * DEFAULT_GOOGLE_PRICING["text_search"].price_per_thousand
                + 2 * DEFAULT_GOOGLE_PRICING["place_details"].price_per_thousand) / 1_000
    assert t.google_cost() == pytest.approx(expected)
    assert t.total_cost() == pytest.approx(expected)


def test_reset_clears_everything():
    t = CostTracker()
    t.record_openai("gpt-5.4", "x", 1, 1)
    t.record_google("text_search")
    t.record_openai_failure()
    t.reset()
    assert t.openai_request_count == 0 and sum(t.google_requests.values()) == 0 and t.failed_openai_requests == 0


def test_simulation():
    r = simulate_monthly(SimulationInputs(
        restaurants=100,
        reviews_per_restaurant=40,
        subscription_price=29.0,
        avg_input_tokens_per_review=3_000,
        avg_output_tokens_per_review=1_500,
        model_pricing=DEFAULT_MODEL_PRICING["gpt-5.4"],
        google_details_requests_per_restaurant=30,
        google_details_price_per_thousand=25.0,
    ))
    per_review = (3_000 * 2.5 + 1_500 * 15) / 1e6  # $0.03
    assert r.ai_cost_per_review == pytest.approx(per_review)
    assert r.monthly_ai_cost == pytest.approx(100 * 40 * per_review)  # $120
    assert r.monthly_google_cost == pytest.approx(3_000 * 25 / 1_000)  # $75
    assert r.monthly_revenue == pytest.approx(2_900)
    assert r.monthly_api_cost == pytest.approx(195)
    assert r.revenue_after_api_costs == pytest.approx(2_705)
    assert r.api_cost_share_of_revenue == pytest.approx(195 / 2_900)
    assert r.api_cost_per_restaurant == pytest.approx(1.95)


def test_simulation_free_cap_and_zero_revenue():
    r = simulate_monthly(SimulationInputs(
        restaurants=10, reviews_per_restaurant=0, subscription_price=0,
        avg_input_tokens_per_review=0, avg_output_tokens_per_review=0,
        model_pricing=DEFAULT_MODEL_PRICING["gpt-5.4-mini"],
        google_details_requests_per_restaurant=30, google_free_monthly_calls=1_000,
    ))
    assert r.monthly_google_cost == 0.0
    assert r.api_cost_share_of_revenue == 0.0
