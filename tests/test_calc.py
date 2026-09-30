import pytest
import asyncio

import main
from calculator import payouts, premium_a, premium_b
from main import QuoteRequest, detect_message_language

def test_language_detection():
    assert detect_message_language("main delivery rider hun, 45 ghante kaam karta hoon", "en") == "hinglish"
    assert detect_message_language("I work as a delivery rider and I am 24", "hinglish") == "en"
    assert detect_message_language("naan delivery rider-a velai seyyaren", "en") == "tanglish"

def test_calc():
    # A 100000, rider, 45h, no night -> 19
    assert premium_a(100000, "delivery_rider", 45, False) == 19
    # A 100000, rider, 45h, night -> 23
    assert premium_a(100000, "delivery_rider", 45, True) == 23
    # A 50000, rider, 45h, no night -> 10
    assert premium_a(50000, "delivery_rider", 45, False) == 10
    # B 500, rider, age 24 -> 7
    assert premium_b(500, "delivery_rider", 24) == 7
    # A 50000, campus, 18h, no night -> 4
    assert premium_a(50000, "campus_worker", 18, False) == 4
    # B 300, campus, age 19 -> 3
    assert premium_b(300, "campus_worker", 19) == 3
    
    # A 100000 / B 500, rider, 30h, age 35 -> 15 / 9
    assert premium_a(100000, "delivery_rider", 30, False) == 15
    assert premium_b(500, "delivery_rider", 35) == 9
    
    # B 300, campus, age 50 -> 5
    assert premium_b(300, "campus_worker", 50) == 5

    # Also test that the guard turns "do you have bike insurance?" into the fixed refusal.
    # This will be tested in test_guard.py or similar, but the prompt says to test it here.
    import guard
    assert guard.check_guard("do you have bike insurance?") is not None

def test_requested_tier_prices():
    rider_a = [premium_a(tier, "delivery_rider", 45, False) for tier in [25000, 50000, 100000, 200000]]
    rider_b = [premium_b(tier, "delivery_rider", 24) for tier in [300, 500, 1000]]
    campus_a = [premium_a(tier, "campus_worker", 18, False) for tier in [25000, 50000, 100000, 200000]]
    campus_b = [premium_b(tier, "campus_worker", 19) for tier in [300, 500, 1000]]
    assert rider_a == [5, 10, 19, 38]
    assert rider_b == [5, 7, 14]
    assert campus_a == [2, 4, 7, 13]
    assert campus_b == [3, 5, 9]

def test_payouts():
    assert payouts("A", 200000) == [
        "₹2,00,000 lump sum for death or permanent disability",
        "Up to ₹40,000 for a 24+ hour accident hospital stay"
    ]
    assert payouts("B", 1000) == ["₹1,000/day for up to 7 days (up to ₹7,000 total)"]

def test_quote_reuses_profile_without_llm(monkeypatch):
    session_id = "quote-test"
    main.sessions[session_id] = {
        "profile": {
            "occupation": "delivery_rider",
            "hours_per_week": 45,
            "night_work": False,
            "age": 24
        },
        "stage": "done",
        "meter": {"tokens_total": 0, "llm_calls": 0},
        "last_question": None
    }

    def fail_if_called(*args, **kwargs):
        raise AssertionError("/quote must not call the LLM")

    monkeypatch.setattr(main, "phrase_intro", fail_if_called)
    result = asyncio.run(main.quote(QuoteRequest(session_id=session_id, product_id="A", tier=200000)))
    assert result == {
        "week": 38,
        "day": 5.43,
        "year": 1976,
        "payout_lines": [
            "₹2,00,000 lump sum for death or permanent disability",
            "Up to ₹40,000 for a 24+ hour accident hospital stay"
        ]
    }
    assert main.sessions[session_id]["meter"] == {"tokens_total": 0, "llm_calls": 0}
