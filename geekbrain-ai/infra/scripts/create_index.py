#!/usr/bin/env python3
"""Create the vector index in OpenSearch Serverless for Bedrock KB.

Uses opensearch-py client with SigV4 auth for reliable AOSS access.
Retries on 403 because data access policies can take minutes to propagate.
"""
import json
import sys
import time
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def get_client(endpoint, region):
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        "aoss",
        session_token=credentials.token,
    )

    host = endpoint.replace("https://", "").replace("http://", "")

    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
    )


def create_index(client, index_name):
    body = {
        "settings": {
            "index": {
                "number_of_shards": 2,
                "number_of_replicas": 0,
                "knn": True,
                "knn.algo_param.ef_search": 512,
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "engine": "faiss",
                        "name": "hnsw",
                        "parameters": {"m": 16, "ef_construction": 512},
                        "space_type": "l2",
                    },
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                "AMAZON_BEDROCK_METADATA": {"type": "text"},
            }
        },
    }

    client.indices.create(index=index_name, body=body)


def main():
    if len(sys.argv) < 2:
        print("Usage: create_index.py <collection_endpoint>", file=sys.stderr)
        sys.exit(1)

    endpoint = sys.argv[1]
    index_name = "bedrock-knowledge-base-default-index"
    region = boto3.Session().region_name or "us-east-1"

    session = boto3.Session()
    sts = session.client("sts")
    identity = sts.get_caller_identity()
    print(f"Running as: {identity['Arn']}")

    max_attempts = 10
    wait_seconds = 30

    for attempt in range(1, max_attempts + 1):
        try:
            client = get_client(endpoint, region)

            if client.indices.exists(index=index_name):
                print("Index already exists — skipping.")
                return

            create_index(client, index_name)
            print("Index created successfully.")
            return

        except Exception as e:
            error_str = str(e)
            if "resource_already_exists_exception" in error_str:
                print("Index already exists — skipping.")
                return
            if ("403" in error_str or "Forbidden" in error_str) and attempt < max_attempts:
                print(f"[{attempt}/{max_attempts}] 403 — data access policy not yet active. Waiting {wait_seconds}s...")
                time.sleep(wait_seconds)
                continue
            print(f"FATAL (attempt {attempt}): {error_str}", file=sys.stderr)
            sys.exit(1)

    print(f"Exhausted {max_attempts} attempts. Access policy never propagated.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
