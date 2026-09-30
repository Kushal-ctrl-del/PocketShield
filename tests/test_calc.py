import pytest
from calculator import premium_a, premium_b
from main import detect_message_language

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
