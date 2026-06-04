#!/usr/bin/env python3
"""
Script to perform fail-over operation using NMS API.
Calls the fail-over endpoint on porta with ipa as the peer IP.
"""

import logging
import time

from cluster_client.config import config
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def fail_over(node: Node) -> None:
    """
    Call the fail-over endpoint with retry logic.

    Args:
        node: Node object with connection details

    Raises:
        RuntimeError: If the API returns HTTP 400 or unexpected response, or max retries exceeded
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/fail-over"
    logger.debug(f"fail_over called - Node(port={node.port}, ip={node.ip})")

    data = {"peerIp": node.ip}
    retry_count = 0
    max_retries = config.fail_over_max_retries

    while retry_count < max_retries:
        api_response = make_single_api_request(
            url=url, bearer_token=node.token, method="POST", data=data
        )

        # Get HTTP status code if present (added by make_single_api_request for error responses)
        http_status = api_response.get("_http_status_code", 200)

        # Parse the response - check statusMessage and error fields
        status_message = api_response.get("statusMessage", "")
        error_field = api_response.get("error", "")

        # Check for LeaderFollower Job Active - retry after delay
        if "LeaderFollower Job Active, cannot Fail-Over" in (
            status_message or error_field
        ):
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"⚠ LeaderFollower Job Active, waiting {config.fail_over_retry_delay} seconds before retry (attempt {retry_count}/{max_retries})..."
                )
                time.sleep(config.fail_over_retry_delay)
                continue
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded while waiting for LeaderFollower Job to complete"
                )
                raise RuntimeError(
                    "fail_over failed: Max retries exceeded - LeaderFollower Job still active"
                )

        # Check for HTTP 400 error
        if http_status == 400:
            message = (status_message or error_field or "Unknown error").strip()
            logger.error(f"HTTP 400 Bad Request: {message}")
            raise RuntimeError(f"fail_over returned 400: {message}")

        # Check for success message
        if status_message == "OKAY: Failover successfully started.":
            logger.debug("✓ Failover successfully started")
            return

        # Any other response is unexpected
        message = (
            (status_message or error_field).strip()
            if (status_message or error_field)
            else "Unknown response"
        )
        logger.error(f"Unexpected fail_over response: {message}")
        raise RuntimeError(f"Unexpected fail_over response: {message}")

    # If we exit the loop without returning, we've exceeded max retries
    logger.error(f"Max retries ({max_retries}) exceeded")
    raise RuntimeError("fail_over failed: Max retries exceeded")
