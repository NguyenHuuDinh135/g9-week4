#!/usr/bin/env python3
"""Create the vector index in OpenSearch Serverless for Bedrock KB."""
import json
import sys
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib.request
import urllib.error


def main():
    if len(sys.argv) < 2:
        print("Usage: create_index.py <collection_endpoint>", file=sys.stderr)
        sys.exit(1)

    endpoint = sys.argv[1]  # e.g. https://xxx.us-east-1.aoss.amazonaws.com
    index_name = "bedrock-knowledge-base-default-index"

    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.region_name or "us-east-1"

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

    try:
        with urllib.request.urlopen(req) as response:
            print(f"Index created: {response.read().decode()}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if "resource_already_exists_exception" in error_body:
            print("Index already exists, skipping.")
        else:
            print(f"Error {e.code}: {error_body}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
