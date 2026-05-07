"""Unit tests for conversation memory module."""

import pytest
from src.memory.conversation import ConversationMemory


class TestConversationMemory:
    def test_initial_state_is_empty(self):
        mem = ConversationMemory(window_size=5)
        assert mem.get_history() == []
        assert mem.turn_count == 0

    def test_add_single_turn(self):
        mem = ConversationMemory(window_size=5)
        mem.add_turn("user", "Hello")
        mem.add_turn("assistant", "Hi there!")
        assert mem.turn_count == 1
        history = mem.get_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there!"}

    def test_sliding_window_evicts_old_turns(self):
        mem = ConversationMemory(window_size=2)
        for i in range(5):
            mem.add_turn("user", f"Question {i}")
            mem.add_turn("assistant", f"Answer {i}")

        history = mem.get_history()
        assert len(history) <= 4
        assert "Question 4" in history[-2]["content"]

    def test_get_last_n_turns(self):
        mem = ConversationMemory(window_size=5)
        for i in range(5):
            mem.add_turn("user", f"Q{i}")
            mem.add_turn("assistant", f"A{i}")

        last_2 = mem.get_last_n_turns(2)
        assert len(last_2) == 4
        assert last_2[0]["content"] == "Q3"
        assert last_2[-1]["content"] == "A4"

    def test_clear_resets_history(self):
        mem = ConversationMemory(window_size=5)
        mem.add_turn("user", "Hello")
        mem.add_turn("assistant", "Hi")
        mem.clear()
        assert mem.get_history() == []
        assert mem.turn_count == 0
