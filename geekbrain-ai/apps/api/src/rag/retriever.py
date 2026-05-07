import boto3
from src.config import AWS_REGION, BEDROCK_KB_ID, RETRIEVAL_TOP_K


def retrieve_from_kb(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """Retrieve relevant chunks from Bedrock Knowledge Base."""
    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

    response = client.retrieve(
        knowledgeBaseId=BEDROCK_KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": top_k}
        },
    )

    results = []
    for item in response.get("retrievalResults", []):
        results.append(
            {
                "content": item["content"]["text"],
                "score": item.get("score", 0),
                "source": item.get("location", {})
                .get("s3Location", {})
                .get("uri", "unknown"),
            }
        )

    return results


def format_context(results: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    if not results:
        return "No relevant documents found."

    parts = []
    for i, r in enumerate(results, 1):
        source_file = r["source"].split("/")[-1] if "/" in r["source"] else r["source"]
        parts.append(f"[Document {i} - {source_file}]\n{r['content']}")

    return "\n\n---\n\n".join(parts)
