import json
import re

import boto3

from src.config import AWS_REGION, BEDROCK_MODEL_ID, SYSTEM_PROMPT
from src.memory.conversation import ConversationMemory
from src.rag.retriever import format_context, retrieve_from_kb
from src.tools.database_tool import get_schema_info, query_database
from src.tools.metrics_tool import get_service_metrics, get_service_status

TOOL_DEFINITIONS = [
    {
        "toolSpec": {
            "name": "query_database",
            "description": "Query the SQLite database for HISTORICAL structured data: past monthly costs, incident records, SLA target numbers, daily metrics. Use this for questions about dollar amounts, cost breakdowns, incident history, SLA targets. NOT for current/live system state.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": f"SQL SELECT query to execute. {get_schema_info()}",
                        }
                    },
                    "required": ["sql"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_service_status",
            "description": "Get CURRENT LIVE status of a service RIGHT NOW: uptime percentage, active alerts, health status (healthy/degraded). Use for questions about whether a service is currently up, what alerts are firing, current health.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Service name: PaymentGW, OrderSvc, AuthSvc, NotificationSvc, ReportingSvc, or FraudDetector",
                        }
                    },
                    "required": ["service_name"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_service_metrics",
            "description": "Get CURRENT LIVE performance metrics of a service RIGHT NOW: p50/p95/p99 latency, error rate, requests per minute, CPU, memory usage. Use for questions about current latency, current error rates, current throughput.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Service name: PaymentGW, OrderSvc, AuthSvc, NotificationSvc, ReportingSvc, or FraudDetector",
                        }
                    },
                    "required": ["service_name"],
                }
            },
        }
    },
]


class Agent:
    """Orchestrator agent that routes questions to KB, tools, or both."""

    def __init__(self):
        self.memory = ConversationMemory()
        self.client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    def answer(self, user_query: str) -> str:
        """Process a user question through the full RAG + Tools pipeline."""
        kb_context = self._retrieve_context(user_query)

        response = self._call_with_tools(user_query, kb_context)

        self.memory.add_turn("user", user_query)
        self.memory.add_turn("assistant", response)

        return response

    def _retrieve_context(self, query: str) -> str:
        """Retrieve relevant documents from Bedrock KB."""
        try:
            results = retrieve_from_kb(query)
            return format_context(results)
        except Exception as e:
            return f"[KB retrieval failed: {e}]"

    def _call_with_tools(self, user_query: str, kb_context: str) -> str:
        """Call Claude with tool use capability, handling tool calls iteratively."""
        messages = []

        history = self.memory.get_last_n_turns()
        for turn in history:
            messages.append({"role": turn["role"], "content": [{"text": turn["content"]}]})

        user_content = f"Question: {user_query}"
        if kb_context:
            user_content += f"\n\n## Retrieved Documents (from Knowledge Base)\n{kb_context}"

        messages.append({"role": "user", "content": [{"text": user_content}]})

        response = self.client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOL_DEFINITIONS},
            inferenceConfig={"maxTokens": 2048, "temperature": 0.1},
        )

        max_iterations = 5
        iteration = 0

        while response["stopReason"] == "tool_use" and iteration < max_iterations:
            iteration += 1
            assistant_message = response["output"]["message"]
            messages.append(assistant_message)

            tool_results = []
            for block in assistant_message["content"]:
                if "toolUse" in block:
                    tool_use = block["toolUse"]
                    result = self._execute_tool(tool_use["name"], tool_use["input"])
                    tool_results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use["toolUseId"],
                                "content": [{"json": result}],
                            }
                        }
                    )

            messages.append({"role": "user", "content": tool_results})

            response = self.client.converse(
                modelId=BEDROCK_MODEL_ID,
                system=[{"text": SYSTEM_PROMPT}],
                messages=messages,
                toolConfig={"tools": TOOL_DEFINITIONS},
                inferenceConfig={"maxTokens": 2048, "temperature": 0.1},
            )

        final_text = ""
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                final_text += block["text"]

        return final_text

    def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a tool call and return the result."""
        if tool_name == "query_database":
            return query_database(tool_input["sql"])
        elif tool_name == "get_service_status":
            return get_service_status(tool_input["service_name"])
        elif tool_name == "get_service_metrics":
            return get_service_metrics(tool_input["service_name"])
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def reset_memory(self) -> None:
        """Clear conversation history."""
        self.memory.clear()
