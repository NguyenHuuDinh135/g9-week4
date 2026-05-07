from collections import deque
from dataclasses import dataclass, field

from src.config import MEMORY_WINDOW_SIZE


@dataclass
class ConversationMemory:
    """Sliding window conversation memory (last N turns)."""

    window_size: int = MEMORY_WINDOW_SIZE
    _history: deque = field(default_factory=lambda: deque())

    def __post_init__(self):
        self._history = deque(maxlen=self.window_size * 2)

    def add_turn(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self._history.append({"role": role, "content": content})

    def get_history(self) -> list[dict]:
        """Get conversation history as list of messages."""
        return list(self._history)

    def get_last_n_turns(self, n: int | None = None) -> list[dict]:
        """Get last N complete turns (user + assistant pairs)."""
        if n is None:
            n = self.window_size

        history = list(self._history)
        max_messages = n * 2
        if len(history) > max_messages:
            return history[-max_messages:]
        return history

    def clear(self) -> None:
        """Clear conversation history."""
        self._history.clear()

    @property
    def turn_count(self) -> int:
        """Number of complete turns (user+assistant pairs)."""
        return len(self._history) // 2
