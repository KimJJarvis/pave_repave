#!/usr/bin/env python3
"""
Script to leave an HSA cluster using NMS API.
Retrieves an integration token and calls the leave-cluster-hsa endpoint.
"""

import argparse
import sys
import json

from node import Node
from make_api_request import make_api_request


def leave_cluster_hsa(node: Node, integration_token: str) -> None:
    """
    Call the leave-cluster-hsa endpoint.

    Args:
        node: Node object with connection details
        integration_token: Integration token
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/leave-cluster-hsa"
    print(f"Calling leave-cluster-hsa on {url}...", file=sys.stderr)

    data = {"force": True, "ip": node.ip, "token": integration_token}

    response = make_api_request(url, node.token, method="POST", data=data)
    print(
        f"✓ leave-cluster-hsa completed: {response.get('status', 'unknown')}",
        file=sys.stderr,
    )


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting leave-cluster-hsa.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(description="Leave an HSA cluster using NMS API")
    parser.add_argument(
        "--token", required=True, help="Bearer token for authentication"
    )
    parser.add_argument(
        "--ip", required=True, help="IP address (dot format)"
    )
    parser.add_argument(
        "--port", required=True, type=int, help="Port number for host"
    )
    parser.add_argument(
        "--integration_token", required=True, help="Integration token"
    )

    args = parser.parse_args()

    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Token: {args.token[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   IP: {args.ip}", file=sys.stderr)
    print(f"[DEBUG]   Port: {args.port}", file=sys.stderr)
    print(f"[DEBUG]   Integration Token: {args.integration_token[:20]}...", file=sys.stderr)

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"

    print("=" * 60, file=sys.stderr)
    print("Leave Cluster HSA Workflow", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Node: {base_url} (forwarded to {node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Call leave-cluster-hsa
    print("\nCalling leave-cluster-hsa...", file=sys.stderr)
    leave_cluster_hsa(node, args.integration_token)

    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Operation completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob
