import logging
import time

from cluster_client.config import config
from cluster_client.make_single_api_request import make_single_api_request
from cluster_client.node import Node

logger = logging.getLogger(__name__)


def fail_over(node: Node) -> None:
    """
    Call the fail-over endpoint with retry logic.

    Performs a fail-over operation by calling the cluster-manager/fail-over API endpoint.
    Automatically retries if a LeaderFollower Job is active, waiting between attempts.

    API Endpoint:
        POST /api/v3/cluster-manager/fail-over

    Args:
        node: Node object containing connection details (port, ip, token)

    Returns:
        None

    Raises:
        RuntimeError: If the API returns HTTP 400, an unexpected response,
                      or max retries exceeded waiting for LeaderFollower Job to complete
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/fail-over"

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
                error_message = "fail_over failed: Max retries exceeded - LeaderFollower Job still active"
                logger.error(error_message)
                raise RuntimeError(error_message)

        # Check for HTTP 400 error
        if http_status == 400:
            message = (status_message or error_field or "Unknown error").strip()
            error_message = f"fail_over returned 400: {message}"
            logger.error(error_message)
            raise RuntimeError(error_message)

        # Check for success message
        if status_message == "OKAY: Failover successfully started.":
            return

        # Any other response is unexpected
        message = (
            (status_message or error_field).strip()
            if (status_message or error_field)
            else "Unknown response"
        )
        error_message = f"Unexpected fail_over response: {message}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # If we exit the loop without returning, we've exceeded max retries
    error_message = "fail_over failed: Max retries exceeded"
    logger.error(error_message)
    raise RuntimeError(error_message)
