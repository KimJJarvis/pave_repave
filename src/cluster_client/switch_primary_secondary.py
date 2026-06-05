#!/usr/bin/env python3
"""
Script to perform switch-primary-secondary operation using NMS API.
Determines the peer ID and calls the switch-primary-secondary endpoint on porta.
"""

import logging

from cluster_client.config import config
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node
from cluster_client.peer_info import get_id

logger = logging.getLogger(__name__)


def switch_primary_secondary(peer: Node) -> None:
    """
    Call the switch-primary-secondary endpoint with retry logic.

    The function implements retry logic for transient conditions such as active
    LeaderFollower jobs or incomplete fail over operations.

    API Endpoint:
        POST /api/v3/cluster-manager/switch-primary-secondary

    Args:
        peer: Node object with connection details

    Raises:
        RuntimeError: Raised in the following scenarios:
            - Could not obtain peer information
            - HTTP 400 Bad Request from the API
            - Max retries exceeded while waiting for LeaderFollower Job to complete
            - Max retries exceeded while waiting for fail over to complete
            - Unexpected API response format or content
            - Max retries exceeded for any other reason
    """
    import time

    # Get the peer ID from the node
    id = get_id(peer)

    host = config.host if config.port_forward else peer.ip
    base_url = f"https://{host}:{peer.port}"
    url = f"{base_url}/api/v3/cluster-manager/switch-primary-secondary"

    data = {"peerId": str(id)}
    retry_count = 0
    max_retries = config.switch_primary_secondary_max_retries

    while retry_count < max_retries:
        api_response = make_single_api_request(
            url=url, bearer_token=peer.token, method="POST", data=data
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
                error_message = "switch_primary_secondary failed: Max retries exceeded - LeaderFollower Job still active"
                logger.error(error_message)
                raise RuntimeError(error_message)

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
                error_message = "switch_primary_secondary failed: Max retries exceeded - Fail over not complete"
                logger.error(error_message)
                raise RuntimeError(error_message)

        # Check for other 400 errors
        if http_status == 400:
            message = (
                (status_message or error_field or message_field).strip()
                if (status_message or error_field or message_field)
                else "Unknown error"
            )
            error_message = f"switch_primary_secondary returned 400: {message}"
            logger.error(error_message)
            raise RuntimeError(error_message)

        # Check for success message
        if (
            message_field
            == "The primary / secondary appliance roles on this peer have been switched."
        ):
            return

        # Any other response is unexpected
        message = (
            (status_message or error_field or message_field).strip()
            if (status_message or error_field or message_field)
            else "Unknown response"
        )
        error_message = f"Unexpected switch_primary_secondary response: {message}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # If we exit the loop without returning, we've exceeded max retries
    error_message = "switch_primary_secondary failed: Max retries exceeded"
    logger.error(error_message)
    raise RuntimeError(error_message)
