#!/usr/bin/env python3
"""Create the vector index in OpenSearch Serverless for Bedrock KB.

Runs OUTSIDE of Terraform as a CI step to avoid provisioner failures.
Retries on 403 because OpenSearch Serverless data access policies
can take 2-5 minutes to propagate after collection creation.
"""
import json
import sys
import time
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib.request
import urllib.error


def create_index(endpoint, index_name, credentials, region):
    url = f"{endpoint}/{index_name}"

    body = json.dumps({
        "settings": {
            "index": {
                "number_of_shards": 2,
                "number_of_replicas": 0,
                "knn": True,
                "knn.algo_param.ef_search": 512
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
                        "parameters": {
                            "m": 16,
                            "ef_construction": 512
                        },
                        "space_type": "l2"
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "text"
                }
            }
        }
    })

    request = AWSRequest(
        method="PUT",
        url=url,
        data=body,
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(credentials, "aoss", region).add_auth(request)

    req = urllib.request.Request(
        url=url,
        data=body.encode(),
        headers=dict(request.headers),
        method="PUT"
    )

    with urllib.request.urlopen(req) as response:
        return response.read().decode()


def main():
    if len(sys.argv) < 2:
        print("Usage: create_index.py <collection_endpoint>", file=sys.stderr)
        sys.exit(1)

    endpoint = sys.argv[1]
    index_name = "bedrock-knowledge-base-default-index"

    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.region_name or "us-east-1"

    max_attempts = 10
    wait_seconds = 30

    for attempt in range(1, max_attempts + 1):
        try:
            result = create_index(endpoint, index_name, credentials, region)
            print(f"Index created successfully: {result}")
            return
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            if "resource_already_exists_exception" in error_body:
                print("Index already exists — skipping.")
                return
            if e.code == 403 and attempt < max_attempts:
                print(f"[{attempt}/{max_attempts}] 403 — data access policy not yet active. Waiting {wait_seconds}s...")
                time.sleep(wait_seconds)
                credentials = session.get_credentials().get_frozen_credentials()
                continue
            print(f"FATAL: HTTP {e.code}: {error_body}", file=sys.stderr)
            sys.exit(1)

    print(f"Exhausted {max_attempts} attempts over {max_attempts * wait_seconds}s. Access policy never propagated.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
