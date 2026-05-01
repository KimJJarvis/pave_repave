#!/usr/bin/env python3
"""
Common API request handler for NMS API calls.
Provides SSL context handling, error handling, and debug logging.
"""

import sys
import json
import urllib.request
import urllib.error
import ssl
from typing import Dict, Any, Optional


def make_api_request(
    url: str,
    bearer_token: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make an API request to the NMS API.
    
    Args:
        url: The full URL to request
        bearer_token: The bearer token for authentication
        method: HTTP method (GET or POST)
        data: Optional data dictionary for POST requests
        
    Returns:
        Response data as dictionary
        
    Raises:
        SystemExit: If the request fails
    """
    print(f"[DEBUG] Making {method} request to: {url}", file=sys.stderr)
    if data:
        print(f"[DEBUG] Request data: {json.dumps(data, indent=2)}", file=sys.stderr)
    
    # Create SSL context that doesn't verify certificates (equivalent to curl -k)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Prepare headers
    headers = {
        "Accept": "application/json",
        "Authorization": f"bearer {bearer_token}"
    }
    
    # Prepare request data
    request_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        request_data = json.dumps(data).encode('utf-8')
    
    # Create request
    request = urllib.request.Request(
        url,
        data=request_data,
        headers=headers,
        method=method
    )
    
    print(f"[DEBUG] Sending request...", file=sys.stderr)
    try:
        # Make the request with timeout
        with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
            print(f"[DEBUG] Response status: {response.status}", file=sys.stderr)
            response_data = response.read().decode('utf-8')
            print(f"[DEBUG] Response data: {response_data}", file=sys.stderr)
            return json.loads(response_data)
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[ERROR] HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        print(f"[ERROR] URL: {url}", file=sys.stderr)
        print(f"[ERROR] Response: {error_body}", file=sys.stderr)
        sys.exit(1)
        
    except urllib.error.URLError as e:
        print(f"[ERROR] URL Error: {e.reason}", file=sys.stderr)
        print(f"[ERROR] URL: {url}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON Decode Error: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"[ERROR] Request timed out after 30 seconds", file=sys.stderr)
        print(f"[ERROR] URL: {url}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"[ERROR] URL: {url}", file=sys.stderr)
        sys.exit(1)

# Made with Bob
