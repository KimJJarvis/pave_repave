#!/usr/bin/env python3
"""
Script to perform switch-primary-secondary operation using NMS API.
Determines the peer ID and calls the switch-primary-secondary endpoint on porta.
"""

import argparse
import sys
import json

from node import Node
from response import Response
from make_single_api_request import make_single_api_request


def switch_primary_secondary(node: Node, id: int) -> Response:
    """
    Call the switch-primary-secondary endpoint.

    Args:
        node: Node object with connection details
        id: Peer ID
        
    Returns:
        Response object with message and status code
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/switch-primary-secondary"
    print(f"Calling switch-primary-secondary on {url}...", file=sys.stderr)

    data = {"peerId": str(id)}

    api_response = make_single_api_request(url, node.token, method="POST", data=data)
    
    # Get HTTP status code if present (added by make_single_api_request for error responses)
    http_status = api_response.get("_http_status_code", 200)
    
    # Parse the response - check statusMessage, message, and error fields
    status_message = api_response.get("statusMessage", "")
    message_field = api_response.get("message", "")
    error_field = api_response.get("error", "")
    
    # Determine message and code based on response
    if message_field == "The primary / secondary appliance roles on this peer have been switched.":
        message = "The primary / secondary appliance roles on this peer have been switched"
        code = 200
    elif "LeaderFollower Job Active, cannot switch-primary-secondary" in (status_message or error_field):
        message = "LeaderFollower Job Active, cannot switch-primary-secondary"
        code = http_status  # Use actual HTTP status code (likely 400)
    else:
        # For all other responses, copy the message and use the HTTP status code
        # Prefer statusMessage, then error, then message field
        message = (status_message or error_field or message_field).strip() if (status_message or error_field or message_field) else "Unknown response"
        code = http_status
    
    response = Response(message=message, code=code)
    print(
        f"✓ switch-primary-secondary completed: {response.message} (code: {response.code})",
        file=sys.stderr,
    )
    
    return response


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
    response = switch_primary_secondary(node, args.id)

    print("\n" + "=" * 60, file=sys.stderr)
    if response.code == 400:
        print("✓ Operation completed successfully!", file=sys.stderr)
    else:
        print(f"⚠ Operation completed with code {response.code}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Output the response
    print("\nResponse:")
    print(json.dumps({"message": response.message, "code": response.code}, indent=2))


if __name__ == "__main__":
    main()

# Made with Bob
