#!/usr/bin/env python3
"""
Script to query peer information from NMS API v3/peers endpoint.
Equivalent to the get_peer_info.py but using v3/peers instead of cluster-manager/cluster-info.
"""

import logging

from cluster_client.config import config
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node
from cluster_client.status import Status

logger = logging.getLogger(__name__)
# logger.disabled = True  # Completely silences this logger


def _map_active_appliance(active_appliance_str: str) -> int:
    """
    Map activeAppliance string to numeric value.

    Args:
        active_appliance_str: String value ("PRIMARY", "SECONDARY", or other)

    Returns:
        Numeric value: 1 for PRIMARY, 2 for SECONDARY, 0 for UNKNOWN
    """
    if active_appliance_str == "PRIMARY":
        return 1
    elif active_appliance_str == "SECONDARY":
        return 2
    else:
        return 0


def _create_status_from_peer(peer: dict) -> Status:
    """
    Create a Status object from a peer dictionary.

    Args:
        peer: Peer dictionary from API response

    Returns:
        Status object with peer information
    """
    active_appliance_str = peer.get("activeAppliance", "UNKNOWN")
    active_appliance = _map_active_appliance(active_appliance_str)

    return Status(
        active_appliance=active_appliance,
        primary_ip=peer.get("primaryIp", ""),
        secondary_ip=peer.get("secondaryIp", ""),
        id=peer.get("id", 0),
    )


def peer_info1(node: Node) -> Status | None:
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
                return _create_status_from_peer(peer)

        # If there's only one peer, return it regardless of IP match
        if len(peers) == 1:
            peer = peers[0]
            logger.info(
                f"Only one peer exists, returning it: primaryIp={peer.get('primaryIp')}, secondaryIp={peer.get('secondaryIp')}"
            )
            return _create_status_from_peer(peer)

        # No matching peer found
        logger.warning(f"No peer found matching target IP: {target_ip}")

        return None

    except KeyError as e:
        logger.error(f"Missing expected field: {e}")
        return None
