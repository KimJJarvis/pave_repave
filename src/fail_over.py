#!/usr/bin/env python3
"""
Script to perform fail-over operation using NMS API.
Calls the fail-over endpoint on porta with ipa as the peer IP.
"""

import argparse
import sys
import json
import logging

from node import Node
from response import Response
from make_single_api_request import make_single_api_request
from utilities import setup_logging

logger = logging.getLogger(__name__)


def fail_over(node: Node) -> Response:
    """
    Call the fail-over endpoint.
    
    Args:
        node: Node object with connection details
        
    Returns:
        Response object with message and status code
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/fail-over"
    logger.info(f"Calling fail-over on {url}...")
    
    data = {
        "peerIp": node.ip
    }
    
    api_response = make_single_api_request(url, node.token, method="POST", data=data)
    
    # Get HTTP status code if present (added by make_single_api_request for error responses)
    http_status = api_response.get("_http_status_code", 200)
    
    # Parse the response - check statusMessage and error fields
    status_message = api_response.get("statusMessage", "")
    error_field = api_response.get("error", "")
    
    # Determine message and code based on response
    if "LeaderFollower Job Active, cannot Fail-Over" in (status_message or error_field):
        message = "LeaderFollower Job Active, cannot Fail-Over"
        code = http_status
    elif status_message == "OKAY: Failover successfully started.":
        message = "Failover successfully started"
        code = 200
    else:
        # For all other responses, copy the message and use HTTP status code
        message = (status_message or error_field).strip() if (status_message or error_field) else "Unknown response"
        code = http_status
    
    response = Response(message=message, code=code)
    logger.info(f"✓ fail-over initiated: {response.message} (code: {response.code})")
    
    return response


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Perform fail-over operation using NMS API"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log to file instead of console"
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
    
    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)
    
    logger.debug("Starting fail-over.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Token: {args.token[:20]}...")
    logger.debug(f"  IP: {args.ip}")
    logger.debug(f"  Port: {args.port}")
    
    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)
    
    # Construct base URL - requests go to localhost with port forwarding
    base_url = f"https://localhost:{node.port}"
    
    logger.info("=" * 60)
    logger.info("Fail-Over Operation")
    logger.info("=" * 60)
    logger.info(f"Target: {base_url} (forwarded to {node.ip})")
    logger.info(f"Peer IP: {node.ip}")
    logger.info("=" * 60)
    
    # Call fail-over
    logger.info("Calling fail-over...")
    response = fail_over(node)
    
    logger.info("=" * 60)
    if response.code == 200:
        logger.info("✓ Operation completed successfully!")
    else:
        logger.warning(f"⚠ Operation completed with code {response.code}")
    logger.info("=" * 60)
    
    # Output the response to stdout
    print("\nResponse:")
    print(json.dumps({"message": response.message, "code": response.code}, indent=2))


if __name__ == "__main__":
    main()

# Made with Bob