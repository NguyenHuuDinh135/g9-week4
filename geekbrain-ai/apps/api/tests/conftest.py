"""Shared test fixtures for the GeekBrain API tests."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_bedrock():
    """Mock boto3 Bedrock client to avoid real AWS calls."""
    with patch("boto3.client") as mock_client:
        mock_runtime = MagicMock()
        mock_agent_runtime = MagicMock()

        def client_factory(service, **kwargs):
            if service == "bedrock-runtime":
                return mock_runtime
            if service == "bedrock-agent-runtime":
                return mock_agent_runtime
            return MagicMock()

        mock_client.side_effect = client_factory

        mock_runtime.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "content": [{"text": "This is a test response from the assistant."}]
                }
            },
        }

        mock_agent_runtime.retrieve.return_value = {
            "retrievalResults": [
                {
                    "content": {"text": "GeekBrain runs 6 production services."},
                    "score": 0.95,
                    "location": {
                        "s3Location": {"uri": "s3://bucket/company_overview.md"}
                    },
                }
            ]
        }

        yield {
            "runtime": mock_runtime,
            "agent_runtime": mock_agent_runtime,
        }


@pytest.fixture
def mock_bedrock_with_tool_use():
    """Mock Bedrock that triggers a tool call then returns final answer."""
    with patch("boto3.client") as mock_client:
        mock_runtime = MagicMock()
        mock_agent_runtime = MagicMock()

        def client_factory(service, **kwargs):
            if service == "bedrock-runtime":
                return mock_runtime
            if service == "bedrock-agent-runtime":
                return mock_agent_runtime
            return MagicMock()

        mock_client.side_effect = client_factory

        call_count = {"n": 0}

        def converse_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {
                    "stopReason": "tool_use",
                    "output": {
                        "message": {
                            "content": [
                                {
                                    "toolUse": {
                                        "toolUseId": "tool-123",
                                        "name": "query_database",
                                        "input": {
                                            "sql": "SELECT SUM(total_cost) as total FROM monthly_costs WHERE service='PaymentGW' AND month IN ('2026-01','2026-02','2026-03')"
                                        },
                                    }
                                }
                            ]
                        }
                    },
                }
            return {
                "stopReason": "end_turn",
                "output": {
                    "message": {
                        "content": [
                            {"text": "[DB] PaymentGW total cost Q1 2026: $16,500"}
                        ]
                    }
                },
            }

        mock_runtime.converse.side_effect = converse_side_effect

        mock_agent_runtime.retrieve.return_value = {"retrievalResults": []}

        yield {
            "runtime": mock_runtime,
            "agent_runtime": mock_agent_runtime,
        }
