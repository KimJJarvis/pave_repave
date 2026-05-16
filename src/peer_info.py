#!/usr/bin/env python3
"""
Script to query peer information from NMS API v3/peers endpoint.
Equivalent to the get_peer_info.py but using v3/peers instead of cluster-manager/cluster-info.
"""

import argparse
import sys
import json
import logging

from node import Node
from status import Status
from make_single_api_request import make_single_api_request
from utilities import setup_logging

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
    response = make_single_api_request(url, node.token, method="GET")
    
    # Extract peer information
    try:
        if "peers" not in response:
            logger.error("'peers' field not found in response")
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response
        
        peers = response.get("peers", [])
        if not peers:
            logger.error("No peers found in response")
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response
        
        # Search through the peers list to find a match with the target IP
        target_ip = node.ip
        logger.debug(f"Searching for peer matching target IP: {target_ip}")
        
        for peer in peers:
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
                
                logger.info(f"✓ Peer match found: primaryIp={primary_ip}, secondaryIp={secondary_ip}, activeAppliance={active_appliance_str} ({active_appliance}), id={peer_id}")
                
                return Status(
                    found=True,
                    active_appliance=active_appliance,
                    primary_ip=primary_ip,
                    secondary_ip=secondary_ip,
                    id=peer_id
                ), response
        
        # No matching peer found
        logger.info(f"No peer found matching target IP: {target_ip}")
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response
        
    except KeyError as e:
        logger.error(f"Missing expected field: {e}")
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Query peer information from NMS API v3/peers endpoint"
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
        help="IP address"
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
    status, full_response = peer_info(node)
    
    logger.info("=" * 60)
    logger.info("✓ Query completed successfully!")
    logger.info("=" * 60)
    
    # Output the complete JSON response to stdout
    print("\nComplete API Response:")
    print(json.dumps(full_response, indent=2))
    
    # Also output the parsed status for reference to stderr via logger
    logger.info("=" * 60)
    logger.info("Parsed Peer Info Status:")
    logger.info(json.dumps({
        "found": status.found,
        "active_appliance": status.active_appliance,
        "primary_ip": status.primary_ip,
        "secondary_ip": status.secondary_ip,
        "id": status.id
    }, indent=2))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

# Made with Bob