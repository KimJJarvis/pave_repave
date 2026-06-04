#!/usr/bin/env python3
"""
Script to display peer information in a table format.
"""

import logging

from cluster_client.config import config
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def peer_table(peer: Node) -> None:
    """
    Display peer information in a markdown table format.

    Args:
        peer: Node object with connection details
    """
    logger.debug(
        f"peer_table called with node: ip={peer.ip}, port={peer.port}, token={'***' if peer.token else None}"
    )

    # Use config.host if port_forward is enabled, otherwise use peer.ip
    host = config.host if config.port_forward else peer.ip
    base_url = f"https://{host}:{peer.port}"
    url = f"{base_url}/api/v3/peers?activeAppliance=ALL&disabled=MATCH_ALL&master=MATCH_ALL"

    logger.debug(
        f"Querying peers from {base_url}... (port_forward={config.port_forward}, host={host})"
    )

    # Make the API request (GET method)
    response = make_single_api_request(url=url, bearer_token=peer.token, method="GET")

    # Extract peer information
    try:
        if "peers" not in response:
            logger.error("'peers' field not found in response")
            return

        peers = response.get("peers", [])
        if not peers:
            logger.error("No peers found in response")
            return

        # Define column widths for alignment
        col1_width = 10  # ID column
        col2_width = 20  # Primary IP column
        col3_width = 20  # Secondary IP column

        # Build the table
        lines = []

        # Header row
        header = f"| {'ID':<{col1_width}} | {'Primary IP':<{col2_width}} | {'Secondary IP':<{col3_width}} |"
        lines.append(header)

        # Separator row (markdown table format)
        separator = f"|{'-' * (col1_width + 2)}|{'-' * (col2_width + 2)}|{'-' * (col3_width + 2)}|"
        lines.append(separator)

        # Data rows
        for peer_data in peers:
            peer_id = peer_data.get("id", "N/A")
            primary_ip = peer_data.get("primaryIp", "")
            secondary_ip = peer_data.get("secondaryIp", "")
            active_appliance = peer_data.get("activeAppliance", "")

            # Add asterisk to the active appliance IP
            if active_appliance == "PRIMARY":
                primary_ip = f"{primary_ip} (*)"
            elif active_appliance == "SECONDARY":
                secondary_ip = f"{secondary_ip} (*)"

            row = f"| {str(peer_id):<{col1_width}} | {str(primary_ip):<{col2_width}} | {str(secondary_ip):<{col3_width}} |"
            lines.append(row)

        # Print the table with empty lines before and after
        print()
        print("\n".join(lines))
        print()

    except KeyError as e:
        logger.error(f"Missing expected field: {e}")

# Made with Bob
