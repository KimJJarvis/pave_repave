#!/usr/bin/env python3
"""
Script to query peer information from NMS API v3/peers endpoint.
Equivalent to the get_peer_info.py but using v3/peers instead of cluster-manager/cluster-info.
"""

import argparse
import sys
import json
import logging

from cluster_client.node import Node
from cluster_client.status import Status
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.utilities import setup_logging
from cluster_client.get_token import get_token
from cluster_client.config import config

logger = logging.getLogger(__name__)
#logger.disabled = True  # Completely silences this logger


def peer_info(node: Node) -> Status | None:
    """
    Get peer information from the NMS API v3/peers endpoint.

    Args:
        node: Node object with connection details

    Returns:
        Status object with peer information, or None if not found
    """
    logger.debug(
        f"peer_info called with node: ip={node.ip}, port={node.port}, token={'***' if node.token else None}"
    )

    # Use config.host if port_forward is enabled, otherwise use node.ip
    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/peers?activeAppliance=ALL&disabled=MATCH_ALL&master=MATCH_ALL"

    logger.debug(
        f"Querying peers from {base_url}... (port_forward={config.port_forward}, host={host})"
    )

    # Make the API request (GET method)
    response = make_single_api_request(url=url, bearer_token=node.token, method="GET")

    # Extract peer information
    try:
        if "peers" not in response:
            logger.error("'peers' field not found in response")
            return None

        peers = response.get("peers", [])
        if not peers:
            logger.error("No peers found in response")
            return None

        # Search through the peers list to find a match with the target IP
        target_ip = node.ip
        logger.debug(f"Searching for peer matching target IP: {target_ip}")

        for peer in peers:
            # Validate required fields are present
            if "primaryIp" not in peer:
                logger.error("Required field 'primaryIp' not present in peer data")
                return None

            if "id" not in peer:
                logger.error("Required field 'id' not present in peer data")
                return None

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

                logger.debug(
                    f"✓ Peer match found: primaryIp={primary_ip}, secondaryIp={secondary_ip}, activeAppliance={active_appliance_str} ({active_appliance}), id={peer_id}"
                )

                return Status(
                    active_appliance=active_appliance,
                    primary_ip=primary_ip,
                    secondary_ip=secondary_ip,
                    id=peer_id,
                )

        # No matching peer found
        logger.debug(f"No peer found matching target IP: {target_ip}")
        return None

    except KeyError as e:
        logger.error(f"Missing expected field: {e}")
        return None

