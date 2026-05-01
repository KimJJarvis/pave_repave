#!/usr/bin/env python3
"""
Script to perform switch-primary-secondary operation using NMS API.
Determines the peer ID and calls the switch-primary-secondary endpoint on porta.
"""

import argparse
import sys
import json

from node import Node
from make_api_request import make_api_request


def switch_primary_secondary(node: Node, id: int) -> None:
    """
    Call the switch-primary-secondary endpoint.

    Args:
        node: Node object with connection details
        id: Peer ID
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/switch-primary-secondary"
    print(f"Calling switch-primary-secondary on {url}...", file=sys.stderr)

    data = {"peerId": str(id)}

    response = make_api_request(url, node.token, method="POST", data=data)
    print(
        f"✓ switch-primary-secondary completed: {response.get('message', 'unknown')}",
        file=sys.stderr,
    )


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting switch-primary-secondary.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Perform switch-primary-secondary operation using NMS API"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Bearer token for authentication",
    )
    parser.add_argument("--ip", required=True, help="IP address")
    parser.add_argument(
        "--port", required=True, type=int, help="Port number for host"
    )
    parser.add_argument(
        "--id", required=True, type=int, help="Peer ID"
    )

    args = parser.parse_args()

    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Token: {args.token[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   IP: {args.ip}", file=sys.stderr)
    print(f"[DEBUG]   Port: {args.port}", file=sys.stderr)
    print(f"[DEBUG]   ID: {args.id}", file=sys.stderr)

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"

    print("=" * 60, file=sys.stderr)
    print("Switch Primary-Secondary Operation", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Target: {base_url} (forwarded to {node.ip})", file=sys.stderr)
    print(f"Peer ID: {args.id}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Call switch-primary-secondary
    print(f"\nCalling switch-primary-secondary...", file=sys.stderr)
    switch_primary_secondary(node, args.id)

    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Operation completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob
