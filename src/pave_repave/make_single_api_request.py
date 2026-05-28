#!/usr/bin/env python3
"""
Single API request handler for NMS API calls.
Provides SSL context handling, error handling, and debug logging.
Makes a single request without retries.
"""

import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import ssl
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def make_single_api_request(
    url: str,
    bearer_token: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
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
        RuntimeError: If maximum retries (5) are exceeded for 502 errors or network errors
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

    logger.debug(f"Making {method} request to: {url}")
    logger.debug(f"Request port: {port}")
    if data:
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")

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
    max_retries = 5
    retry_delay = 30  # seconds
    
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
                request, context=ssl_context, timeout=30
            ) as response:
                logger.debug(f"Response status: {response.status}")
                response_data = response.read().decode("utf-8")
                parsed_response = json.loads(response_data)
                logger.debug(f"Response data: {json.dumps(parsed_response, indent=2)}")
                return parsed_response

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.debug(f"HTTP Error {e.code}: {e.reason}")
            logger.debug(f"URL: {url}")
            logger.debug(f"Response: {error_body}")

            # Handle 502 Bad Gateway with retry logic
            if e.code == 502:
                if attempt < max_retries - 1:
                    logger.warning(f"HTTP 502 Bad Gateway received. Waiting {retry_delay} seconds before retry...")
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
            except json.JSONDecodeError:
                # If response is not JSON, return a structured error
                return {"error": error_body, "_http_status_code": e.code}

        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
            logger.error(f"URL: {url}")
            raise RuntimeError(f"URL Error: {e.reason}") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            raise ValueError(f"JSON Decode Error: {e}") from e
        except TimeoutError as e:
            logger.error("Request timed out after 30 seconds")
            logger.error(f"URL: {url}")
            raise RuntimeError("Request timed out after 30 seconds") from e
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            logger.error(f"URL: {url}")
            raise RuntimeError(f"Unexpected error: {type(e).__name__}: {e}") from e
    
    # This should never be reached due to the exception handling above
    raise RuntimeError(f"Unexpected exit from retry loop for {url}")
