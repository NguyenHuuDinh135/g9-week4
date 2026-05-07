"""Tests for the FastAPI HTTP server (apps/api/server.py).

RED phase: these tests define the contract for the chat API endpoint
that the frontend will consume.
"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app(mock_bedrock):
    """Create FastAPI app with mocked Bedrock."""
    from src.server import create_app

    return create_app()


@pytest.fixture
async def client(app):
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestChatEndpoint:
    async def test_chat_requires_messages(self, client):
        resp = await client.post("/api/chat", json={})
        assert resp.status_code == 422

    async def test_chat_accepts_valid_request(self, client):
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "What services does GeekBrain run?"}]},
        )
        assert resp.status_code == 200

    async def test_chat_returns_streaming_response(self, client):
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    async def test_chat_stream_contains_text_event(self, client):
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        body = resp.text
        assert "data:" in body

    async def test_chat_with_thread_id_maintains_context(self, client):
        resp = await client.post(
            "/api/chat",
            json={
                "messages": [{"role": "user", "content": "Tell me about PaymentGW"}],
                "thread_id": "thread-abc",
            },
        )
        assert resp.status_code == 200

    async def test_chat_rejects_empty_messages(self, client):
        resp = await client.post(
            "/api/chat",
            json={"messages": []},
        )
        assert resp.status_code == 422


class TestCORSHeaders:
    async def test_cors_allows_localhost(self, client):
        resp = await client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.status_code in (200, 204)
        assert "access-control-allow-origin" in resp.headers
