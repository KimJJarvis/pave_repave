#!/usr/bin/env python3
"""
Script to query peer information from NMS API v3/peers endpoint.
Equivalent to the get_peer_info.py but using v3/peers instead of cluster-manager/cluster-info.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.status import Status
from pave_repave.make_single_api_request import make_single_api_request
from pave_repave.utilities import setup_logging

logger = logging.getLogger(__name__)


def peer_info(node: Node) -> tuple[Status, dict]:
    """
    Get peer information from the NMS API v3/peers endpoint.

    Args:
        node: Node object with connection details

    Returns:
        Tuple of (Status object with peer information, full API response dict)
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/peers?activeAppliance=ALL&disabled=MATCH_ALL&master=MATCH_ALL"

    logger.info(f"Querying peers from {base_url}...")

    # Make the API request (GET method)
    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    # Extract peer information
    try:
        if "peers" not in response:
            msg = "'peers' field not found in response"
            logger.error(msg)
            return (
                Status(
                    found=False,
                    msg=msg
                ),
                response,
            )

        peers = response.get("peers", [])
        if not peers:
            msg = "No peers found in response"
            logger.error(msg)
            return (
                Status(
                    found=False,
                    msg=msg
                ),
                response,
            )

        # Search through the peers list to find a match with the target IP
        target_ip = node.ip
        logger.debug(f"Searching for peer matching target IP: {target_ip}")

        for peer in peers:
            # Validate required fields are present
            if "primaryIp" not in peer:
                msg = "Required field 'primaryIp' not present in peer data"
                logger.error(msg)
                return (
                    Status(
                        found=False,
                        msg=msg
                    ),
                    response,
                )
            
            if "id" not in peer:
                msg = "Required field 'id' not present in peer data"
                logger.error(msg)
                return (
                    Status(
                        found=False,
                        msg=msg
                    ),
                    response,
                )
            
            primary_ip = peer.get("primaryIp", "")
            secondary_ip = peer.get("secondaryIp", "")

            # Check if either primaryIp or secondaryIp matches the target IP
            if primary_ip == target_ip or secondary_ip == target_ip:
                # Map activeAppliance string to numeric value
                # "PRIMARY" = 1, "SECONDARY" = 2, "UNKNOWN" = 0
                active_appliance_str = peer.get("activeAppliance", "UNKNOWN")
                if active_appliance_str == "PRIMARY":
                    active_appliance = 1
                elif active_appliance_str == "SECONDARY":
                    active_appliance = 2
                else:
                    active_appliance = 0

                peer_id = peer.get("id", 0)

                logger.info(
                    f"✓ Peer match found: primaryIp={primary_ip}, secondaryIp={secondary_ip}, activeAppliance={active_appliance_str} ({active_appliance}), id={peer_id}"
                )

                return (
                    Status(
                        found=True,
                        active_appliance=active_appliance,
                        primary_ip=primary_ip,
                        secondary_ip=secondary_ip,
                        id=peer_id,
                    ),
                    response,
                )

        # No matching peer found
        msg = f"No peer found matching target IP: {target_ip}"
        logger.info(msg)
        return (
            Status(
                found=False,
                msg=msg
            ),
            response,
        )

    except KeyError as e:
        msg = f"Missing expected field: {e}"
        logger.error(msg)
        return (
            Status(
                found=False,
                msg=msg
            ),
            response,
        )


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Query peer information from NMS API v3/peers endpoint"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parser.add_argument(
        "--token", required=True, help="Bearer token for authentication"
    )
    parser.add_argument("--ip", required=True, help="IP address")
    parser.add_argument("--port", required=True, type=int, help="Port number for host")

    args = parser.parse_args()

    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    logger.debug("Starting peer-info.py script")
    logger.debug("Arguments parsed:")
    logger.debug(f"  Token: {args.token[:20]}...")
    logger.debug(f"  IP: {args.ip}")
    logger.debug(f"  Port: {args.port}")

    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)

    logger.info("=" * 60)
    logger.info("Peer Info Query (v3/peers)")
    logger.info("=" * 60)
    logger.info(f"Target: https://localhost:{node.port} (forwarded to {node.ip})")
    logger.info("=" * 60)

    # Get peer info
    status, full_response = peer_info(node=node)

    logger.info("=" * 60)
    logger.info("✓ Query completed successfully!")
    logger.info("=" * 60)

    # Also output the parsed status for reference to stderr via logger
    logger.info("=" * 60)
    logger.info("Parsed Peer Info Status:")
    parsed_status = json.dumps(
        {
            "found": status.found,
            "active_appliance": status.active_appliance,
            "primary_ip": status.primary_ip,
            "secondary_ip": status.secondary_ip,
            "id": status.id,
            "msg": status.msg,
        },
        indent=2,
    )
    logger.info(parsed_status)
    logger.info("=" * 60)
    
    # Print parsed status to console (stdout)
    print("\n" + "=" * 60)
    print("Parsed Peer Info Status:")
    print(parsed_status)
    print("=" * 60)
