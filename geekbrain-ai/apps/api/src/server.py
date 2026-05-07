"""FastAPI HTTP server exposing the GeekBrain AI agent as a streaming chat API."""

import json
import re
from collections import OrderedDict
from threading import Lock
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sse_starlette.sse import EventSourceResponse

from src.agent import Agent

MAX_THREADS = 200
MAX_MESSAGE_LENGTH = 10_000
MAX_MESSAGES_PER_REQUEST = 50


class Message(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in {"user", "assistant", "system"}:
            raise ValueError("role must be 'user', 'assistant', or 'system'")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"content exceeds {MAX_MESSAGE_LENGTH} chars")
        return v


class ChatRequest(BaseModel):
    messages: list[Message]
    thread_id: str | None = None

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v: list[Message]) -> list[Message]:
        if not v:
            raise ValueError("messages must not be empty")
        if len(v) > MAX_MESSAGES_PER_REQUEST:
            raise ValueError(f"too many messages (max {MAX_MESSAGES_PER_REQUEST})")
        return v

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) > 64:
            raise ValueError("thread_id too long (max 64 chars)")
        if not re.match(r"^[a-zA-Z0-9\-_]+$", v):
            raise ValueError("thread_id contains invalid characters")
        return v


_threads: OrderedDict[str, Agent] = OrderedDict()
_threads_lock = Lock()


def _get_agent(thread_id: str | None) -> Agent:
    if thread_id is None:
        return Agent()

    with _threads_lock:
        if thread_id in _threads:
            _threads.move_to_end(thread_id)
            return _threads[thread_id]

        if len(_threads) >= MAX_THREADS:
            _threads.popitem(last=False)

        _threads[thread_id] = Agent()
        return _threads[thread_id]


async def _stream_response(agent: Agent, user_message: str) -> AsyncGenerator[dict, None]:
    try:
        response = agent.answer(user_message)
        yield {"data": json.dumps({"type": "text", "content": response})}
    except Exception as e:
        yield {"data": json.dumps({"type": "error", "content": str(e)})}
    yield {"data": json.dumps({"type": "done"})}


def create_app() -> FastAPI:
    app = FastAPI(title="GeekBrain AI API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/chat")
    async def chat(request: ChatRequest):
        agent = _get_agent(request.thread_id)
        user_message = request.messages[-1].content
        return EventSourceResponse(_stream_response(agent, user_message))

    return app


app = create_app()
