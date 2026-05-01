#!/usr/bin/env python3
"""
Script to query cluster-info from NMS API and display peer information.
Equivalent to: curl + jq '(.clusterInfo | fromjson).peer_info.peer_info'
"""

import argparse
import sys
import json

from node import Node
from status import Status
from make_api_request import make_api_request


def get_peer_info(node: Node) -> Status:
    """
    Get peer information from the NMS API.
    
    Args:
        node: Node object with connection details
        
    Returns:
        Status object with peer information
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/cluster-manager/cluster-info"
    
    print(f"Querying cluster-info from {base_url}...", file=sys.stderr)
    
    # Make the API request (GET method)
    response = make_api_request(url, node.token, method="GET")
    
    # Extract and parse the nested JSON
    try:
        if "clusterInfo" not in response:
            print("[ERROR] 'clusterInfo' field not found in response", file=sys.stderr)
            # Return a Status indicating peer not found
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
        
        # Parse the nested JSON string
        cluster_info = json.loads(response["clusterInfo"])
        
        # Navigate to peer_info.peer_info
        if "peer_info" not in cluster_info:
            print("[ERROR] 'peer_info' field not found in clusterInfo", file=sys.stderr)
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
        
        peer_info = cluster_info["peer_info"]
        
        if "peer_info" not in peer_info:
            print("[ERROR] 'peer_info' field not found in peer_info", file=sys.stderr)
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
        
        peer_info_data = peer_info["peer_info"]
        
        # Extract relevant fields
        found = peer_info_data.get("found", False)
        active_appliance = peer_info_data.get("active_appliance", 0)
        primary_ip = peer_info_data.get("primary_ip", "")
        secondary_ip = peer_info_data.get("secondary_ip", "")
        peer_id = peer_info_data.get("id", 0)
        
        print(f"✓ Peer info retrieved: found={found}, active_appliance={active_appliance}, id={peer_id}", file=sys.stderr)
        
        return Status(
            found=found,
            active_appliance=active_appliance,
            primary_ip=primary_ip,
            secondary_ip=secondary_ip,
            id=peer_id
        )
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse nested clusterInfo JSON: {e}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
    except KeyError as e:
        print(f"[ERROR] Missing expected field: {e}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting get-peer-info.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Query cluster-info from NMS API and display peer information"
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
    print("Cluster Info Query", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Target: https://localhost:{node.port} (forwarded to {node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Get peer info
    status = get_peer_info(node)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Query completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Output the status
    print("\nPeer Info Status:")
    print(json.dumps({
        "found": status.found,
        "active_appliance": status.active_appliance,
        "primary_ip": status.primary_ip,
        "secondary_ip": status.secondary_ip,
        "id": status.id
    }, indent=2))


if __name__ == "__main__":
    main()

# Made with Bob