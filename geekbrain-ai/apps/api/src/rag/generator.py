import json

import boto3

from src.config import AWS_REGION, BEDROCK_MODEL_ID, SYSTEM_PROMPT


def generate_response(
    user_query: str,
    context: str,
    tool_results: str | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """Generate a response using Bedrock Claude with context and tool results."""
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    messages = []

    if conversation_history:
        for turn in conversation_history:
            messages.append({"role": turn["role"], "content": [{"text": turn["content"]}]})

    user_content = f"Question: {user_query}\n\n"

    if context:
        user_content += f"## Retrieved Documents\n{context}\n\n"

    if tool_results:
        user_content += f"## Tool Results\n{tool_results}\n\n"

    user_content += "Please answer the question using the information above. Cite sources with [KB], [DB], or [API] prefixes."

    messages.append({"role": "user", "content": [{"text": user_content}]})

    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=messages,
        inferenceConfig={"maxTokens": 2048, "temperature": 0.1},
    )

    return response["output"]["message"]["content"][0]["text"]
