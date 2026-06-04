#!/usr/bin/env python3
"""
Single API request handler for NMS API calls.
Provides SSL context handling, error handling, and debug logging.
Makes a single request without retries.
"""

import json
import logging
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from cluster_client.config import config

logger = logging.getLogger(__name__)
# logger.disabled = True  # Completely silences this logger


def make_single_api_request(
    url: str,
    bearer_token: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make a single API request to the NMS API with retry logic for 502 errors.

    Args:
        url: The full URL to request
        bearer_token: The bearer token for authentication
        method: HTTP method (GET or POST)
        data: Optional data dictionary for POST requests

    Returns:
        Response data as dictionary

    Raises:
        RuntimeError: If maximum retries are exceeded for 502 errors or network errors
        ValueError: If authentication fails or JSON decode errors occur
    """
    parsed_url = urllib.parse.urlparse(url)
    port = parsed_url.port
    if port is None:
        if parsed_url.scheme == "https":
            port = 443
        elif parsed_url.scheme == "http":
            port = 80
        else:
            port = "unknown"

    logger.info(f"Request method: {method} {url}")
    if data:
        logger.info(f"Request data: {json.dumps(data, indent=2)}")

    # Create SSL context that doesn't verify certificates (equivalent to curl -k)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Prepare headers
    headers = {"Accept": "application/json", "Authorization": f"bearer {bearer_token}"}

    # Prepare request data
    request_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        request_data = json.dumps(data).encode("utf-8")

    # Retry logic for 502 errors
    max_retries = config.http_502_max_retries
    retry_delay = config.http_502_retry_delay

    for attempt in range(max_retries):
        # Create request (needs to be recreated for each attempt)
        request = urllib.request.Request(
            url, data=request_data, headers=headers, method=method
        )

        if attempt > 0:
            logger.info(f"Retry attempt {attempt} of {max_retries - 1} after 502 error")

        logger.debug("Sending request...")

        try:
            # Make the request with timeout
            with urllib.request.urlopen(
                request, context=ssl_context, timeout=config.http_timeout_value
            ) as response:
                logger.info(f"Response status: {response.status}")
                try:
                    response_data = response.read().decode("utf-8")
                except UnicodeDecodeError as e:
                    logger.error(f"Unicode Decode Error: {e}")
                    raise ValueError(f"Response contains invalid UTF-8: {e}") from e
                
                try:
                    parsed_response = json.loads(response_data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {e}")
                    logger.error(f"Response data (first 500 chars): {response_data[:500]}")
                    raise ValueError(f"Invalid JSON in response: {e}") from e
                
                logger.info(f"Response data: {json.dumps(parsed_response, indent=2)}")
                return parsed_response

        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
            except UnicodeDecodeError as decode_err:
                logger.error(f"Unicode Decode Error in error response: {decode_err}")
                raise ValueError(f"Error response contains invalid UTF-8: {decode_err}") from decode_err
            logger.info(f"HTTP Error {e.code}: {e.reason}")
            logger.info(f"Response: {error_body}")

            # Handle 502 Bad Gateway with retry logic
            if e.code == 502:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"HTTP 502 Bad Gateway received. Waiting {retry_delay} seconds before retry..."
                    )
                    time.sleep(retry_delay)
                    continue  # Retry the request
                else:
                    # Maximum retries exceeded
                    raise RuntimeError(
                        f"Maximum retries ({max_retries}) exceeded for HTTP 502 Bad Gateway error at {url}"
                    )

            # Raise exception if authentication fails (401 Unauthorized)
            if e.code == 401:
                # Check if token is expired or just invalid
                error_message_lower = error_body.lower()
                if (
                    "token is expired" in error_message_lower
                    or "token expired" in error_message_lower
                ):
                    logger.error("Bearer token expired")
                    raise ValueError("Bearer token expired") from e
                else:
                    logger.error("Invalid bearer token")
                    raise ValueError("Invalid bearer token") from e

            # Parse and return the error response so caller can handle it
            try:
                error_data = json.loads(error_body)
                # Add the HTTP status code to the response
                error_data["_http_status_code"] = e.code
                return error_data
            except json.JSONDecodeError as json_err:
                # If response is not JSON, return a structured error
                logger.warning(f"Error response is not valid JSON: {json_err}")
                logger.debug(f"Error body (first 500 chars): {error_body[:500]}")
                return {"error": error_body, "_http_status_code": e.code}

        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
            logger.error(f"URL: {url}")
            raise RuntimeError(f"URL Error: {e.reason}") from e
        except ValueError:
            # Re-raise ValueError exceptions (from JSON/Unicode decode errors)
            raise
        except TimeoutError as e:
            logger.error(f"Request timed out after {config.http_timeout_value} seconds")
            logger.error(f"URL: {url}")
            raise RuntimeError(f"Request timed out after {config.http_timeout_value} seconds") from e
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            logger.error(f"URL: {url}")
            raise RuntimeError(f"Unexpected error: {type(e).__name__}: {e}") from e

    # This should never be reached due to the exception handling above
    raise RuntimeError(f"Unexpected exit from retry loop for {url}")
