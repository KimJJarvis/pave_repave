#!/usr/bin/env python3
"""
Script to query peer information from NMS API v3/peers endpoint.
Equivalent to the get_peer_info.py but using v3/peers instead of cluster-manager/cluster-info.
"""

import argparse
import sys
import json

from node import Node
from status import Status
from make_api_request import make_api_request


def peer_info(node: Node) -> tuple[Status, dict]:
    """
    Get peer information from the NMS API v3/peers endpoint.
    
    Args:
        node: Node object with connection details
        
    Returns:
        Tuple of (Status object with peer information, full API response dict)
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/peers?activeAppliance=ALL&disabled=MATCH_ALL&master=MATCH_ALL"
    
    print(f"Querying peers from {base_url}...", file=sys.stderr)
    
    # Make the API request (GET method)
    response = make_api_request(url, node.token, method="GET")
    
    # Extract peer information
    try:
        if "peers" not in response:
            print("[ERROR] 'peers' field not found in response", file=sys.stderr)
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response
        
        peers = response.get("peers", [])
        if not peers:
            print("[ERROR] No peers found in response", file=sys.stderr)
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response
        
        # Search through the peers list to find a match with the target IP
        target_ip = node.ip
        print(f"[DEBUG] Searching for peer matching target IP: {target_ip}", file=sys.stderr)
        
        for peer in peers:
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
                
                print(f"✓ Peer match found: primaryIp={primary_ip}, secondaryIp={secondary_ip}, activeAppliance={active_appliance_str} ({active_appliance}), id={peer_id}", file=sys.stderr)
                
                return Status(
                    found=True,
                    active_appliance=active_appliance,
                    primary_ip=primary_ip,
                    secondary_ip=secondary_ip,
                    id=peer_id
                ), response
        
        # No matching peer found
        print(f"[INFO] No peer found matching target IP: {target_ip}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response
        
    except KeyError as e:
        print(f"[ERROR] Missing expected field: {e}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0), response


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting peer-info.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Query peer information from NMS API v3/peers endpoint"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Bearer token for authentication"
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP address"
    )
    parser.add_argument(
        "--port",
        required=True,
        type=int,
        help="Port number for host"
    )
    
    args = parser.parse_args()
    
    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Token: {args.token[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   IP: {args.ip}", file=sys.stderr)
    print(f"[DEBUG]   Port: {args.port}", file=sys.stderr)
    
    # Create Node object
    node = Node(port=args.port, token=args.token, ip=args.ip)
    
    print("=" * 60, file=sys.stderr)
    print("Peer Info Query (v3/peers)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Target: https://localhost:{node.port} (forwarded to {node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Get peer info
    status, full_response = peer_info(node)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Query completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Output the complete JSON response
    print("\nComplete API Response:")
    print(json.dumps(full_response, indent=2))
    
    # Also output the parsed status for reference
    print("\n" + "=" * 60, file=sys.stderr)
    print("Parsed Peer Info Status:", file=sys.stderr)
    print(json.dumps({
        "found": status.found,
        "active_appliance": status.active_appliance,
        "primary_ip": status.primary_ip,
        "secondary_ip": status.secondary_ip,
        "id": status.id
    }, indent=2), file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob