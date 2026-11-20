import json
import os
import pytest
from src.brain.escalation import is_escalation, log_escalation, UnresolvedTurnCounter


def test_is_escalation_true_for_english_keywords():
    assert is_escalation("I want to transfer to a human agent") is True
    assert is_escalation("Please escalate this issue") is True
    assert is_escalation("I cannot resolve this problem") is True


def test_is_escalation_true_for_urdu_keywords():
    assert is_escalation("mujhe agent chahiye") is True
    assert is_escalation("transfer karein please") is True
    assert is_escalation("agent se baat karni hai") is True


def test_is_escalation_false_for_normal_message():
    assert is_escalation("What is the price of iPhone 15?") is False
    assert is_escalation("Mujhe order ki details chahiye") is False
    assert is_escalation("Hello, how are you?") is False


def test_log_escalation_appends_correct_entry(tmp_path):
    path = str(tmp_path / "escalations.json")
    log_escalation("Test issue", [{"role": "user", "content": "help"}], path)
    with open(path) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["issue"] == "Test issue"
    assert "timestamp" in data[0]
    assert data[0]["conversation"] == [{"role": "user", "content": "help"}]


def test_unresolved_turn_counter_increments_and_triggers_at_3():
    counter = UnresolvedTurnCounter()
    assert counter.should_escalate() is False
    counter.increment()
    counter.increment()
    assert counter.should_escalate() is False
    counter.increment()
    assert counter.should_escalate() is True


def test_unresolved_turn_counter_reset():
    counter = UnresolvedTurnCounter()
    counter.increment()
    counter.increment()
    counter.increment()
    assert counter.should_escalate() is True
    counter.reset()
    assert counter.should_escalate() is False
