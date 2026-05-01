#!/usr/bin/env python3
"""
Script to retrieve an integration token from NMS API.
Simplified version that only gets and prints the integration token from porta.
"""

import argparse
import sys
import json

from node import Node
from make_api_request import make_api_request


def get_integration_token(node: Node) -> str:
    """
    Retrieve integration token from the NMS API.
    
    Args:
        node: Node object with connection details
        
    Returns:
        The integration token string
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-orchestrator/integration-token"
    print(f"Getting integration token from {url}...", file=sys.stderr)
    
    response = make_api_request(url, node.token, method="GET")
    
    if "token" not in response:
        print(f"Error: 'token' field not found in response: {response}", file=sys.stderr)
        sys.exit(1)
    
    token = response["token"]
    print(f"✓ Integration token retrieved", file=sys.stderr)
    return token


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting get-integration-token.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Get integration token from NMS API"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Bearer token for authentication"
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP address"
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
    
    # Construct base URL - request goes to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"
    
    print("=" * 60, file=sys.stderr)
    print("Get Integration Token", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Node: {base_url} (forwarded to {node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Get integration token
    print("\nGetting integration token...", file=sys.stderr)
    integration_token = get_integration_token(node)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Operation completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Output the integration token
    print("\nIntegration Token:")
    print(json.dumps({"token": integration_token}, indent=2))


if __name__ == "__main__":
    main()

# Made with Bob