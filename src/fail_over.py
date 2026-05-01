#!/usr/bin/env python3
"""
Script to perform fail-over operation using NMS API.
Calls the fail-over endpoint on porta with ipa as the peer IP.
"""

import argparse
import sys
import json

from node import Node
from make_api_request import make_api_request


def fail_over(node: Node) -> None:
    """
    Call the fail-over endpoint.
    
    Args:
        node: Node object with connection details
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/fail-over"
    print(f"Calling fail-over on {url}...", file=sys.stderr)
    
    data = {
        "peerIp": node.ip
    }
    
    response = make_api_request(url, node.token, method="POST", data=data)
    print(f"✓ fail-over completed", file=sys.stderr)


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting fail-over.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Perform fail-over operation using NMS API"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Bearer token for authentication"
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP address (used as peer IP for fail-over)"
    )
    parser.add_argument(
        "--port",
        required=True,
        type=int,
        help="Port number for host"
    )
    
    args = parser.parse_args()
    
    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Token: {args.token[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   IP: {args.ip}", file=sys.stderr)
    print(f"[DEBUG]   Port: {args.port}", file=sys.stderr)
    
    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)
    
    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"
    
    print("=" * 60, file=sys.stderr)
    print("Fail-Over Operation", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Target: {base_url} (forwarded to {node.ip})", file=sys.stderr)
    print(f"Peer IP: {node.ip}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Call fail-over
    print(f"\nCalling fail-over...", file=sys.stderr)
    fail_over(node)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Operation completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob