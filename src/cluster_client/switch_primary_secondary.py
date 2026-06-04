#!/usr/bin/env python3
"""
Script to perform switch-primary-secondary operation using NMS API.
Determines the peer ID and calls the switch-primary-secondary endpoint on porta.
"""

import argparse
import sys
import json
import logging

from cluster_client.node import Node
from cluster_client.response import Response
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.utilities import setup_logging
from cluster_client.get_token import get_token
from cluster_client.config import config

logger = logging.getLogger(__name__)


def switch_primary_secondary(node: Node, id: int) -> None:
    """
    Call the switch-primary-secondary endpoint with retry logic.

    Args:
        node: Node object with connection details
        id: Peer ID

    Raises:
        RuntimeError: If the API returns HTTP 400 or unexpected response, or max retries exceeded
    """
    import time

    host = config.host if config.port_forward else node.ip
    base_url = f"https://{host}:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/switch-primary-secondary"
    logger.info(f"Calling switch-primary-secondary on {url}...")

    data = {"peerId": str(id)}
    retry_count = 0
    max_retries = config.switch_primary_secondary_max_retries

    while retry_count < max_retries:
        api_response = make_single_api_request(
            url=url, bearer_token=node.token, method="POST", data=data
        )

        # Get HTTP status code if present (added by make_single_api_request for error responses)
        http_status = api_response.get("_http_status_code", 200)

        # Parse the response - check statusMessage, message, and error fields
        status_message = api_response.get("statusMessage", "")
        message_field = api_response.get("message", "")
        error_field = api_response.get("error", "")

        # Check for LeaderFollower Job Active - retry after delay
        if "LeaderFollower Job Active, cannot switch-primary-secondary" in (
            status_message or error_field
        ):
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"⚠ LeaderFollower Job Active, waiting {config.switch_primary_secondary_retry_delay} seconds before retry (attempt {retry_count}/{max_retries})..."
                )
                time.sleep(config.switch_primary_secondary_retry_delay)
                continue
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded while waiting for LeaderFollower Job to complete"
                )
                raise RuntimeError(
                    f"switch_primary_secondary failed: Max retries exceeded - LeaderFollower Job still active"
                )

        # Check for fail over not yet complete - retry after delay
        if "A secondary-leader appliance was not found on this peer" in (
            status_message or error_field or message_field
        ):
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"⚠ Fail over not yet complete, waiting {config.switch_primary_secondary_retry_delay} seconds before retry (attempt {retry_count}/{max_retries})..."
                )
                time.sleep(config.switch_primary_secondary_retry_delay)
                continue
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded while waiting for fail over to complete"
                )
                raise RuntimeError(
                    f"switch_primary_secondary failed: Max retries exceeded - Fail over not complete"
                )

        # Check for other 400 errors
        if http_status == 400:
            message = (
                (status_message or error_field or message_field).strip()
                if (status_message or error_field or message_field)
                else "Unknown error"
            )
            logger.error(f"HTTP 400 Bad Request: {message}")
            raise RuntimeError(f"switch_primary_secondary returned 400: {message}")

        # Check for success message
        if (
            message_field
            == "The primary / secondary appliance roles on this peer have been switched."
        ):
            logger.info("✓ switch-primary-secondary completed successfully")
            return

        # Any other response is unexpected
        message = (
            (status_message or error_field or message_field).strip()
            if (status_message or error_field or message_field)
            else "Unknown response"
        )
        logger.error(f"Unexpected switch_primary_secondary response: {message}")
        raise RuntimeError(f"Unexpected switch_primary_secondary response: {message}")

    # If we exit the loop without returning, we've exceeded max retries
    logger.error(f"Max retries ({max_retries}) exceeded")
    raise RuntimeError(f"switch_primary_secondary failed: Max retries exceeded")

