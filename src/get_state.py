#!/usr/bin/env python3
"""
Script to determine cluster state by querying peer information from multiple nodes.
Queries api/v3/peers on peer, hsa, and spare nodes to determine the current state.
"""

import argparse
import sys
import json

from node import Node
from status import Status
from make_single_api_request import make_single_api_request


def get_peer_info(node: Node, target_ip: str) -> Status:
    """
    Get peer information from the NMS API v3/peers endpoint.
    
    Args:
        node: Node object with connection details
        target_ip: IP address to search for in the peers list
        
    Returns:
        Status object with peer information
    """
    base_url = f"https://localhost:{node.port}"
    url = f"{base_url}/api/v3/peers?activeAppliance=ALL&disabled=MATCH_ALL&master=MATCH_ALL"
    
    print(f"[DEBUG] Querying peers from {base_url} (target IP: {target_ip})...", file=sys.stderr)
    
    try:
        # Make the API request (GET method)
        response = make_single_api_request(url, node.token, method="GET")
        
        # Extract peer information
        if "peers" not in response:
            print(f"[ERROR] 'peers' field not found in response from {base_url}", file=sys.stderr)
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
        
        peers = response.get("peers", [])
        if not peers:
            print(f"[INFO] No peers found in response from {base_url}", file=sys.stderr)
            return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
        
        # Search through the peers list to find a match with the target IP
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
                
                print(f"[DEBUG] ✓ Peer match found: primaryIp={primary_ip}, secondaryIp={secondary_ip}, activeAppliance={active_appliance_str} ({active_appliance}), id={peer_id}", file=sys.stderr)
                
                return Status(
                    found=True,
                    active_appliance=active_appliance,
                    primary_ip=primary_ip,
                    secondary_ip=secondary_ip,
                    id=peer_id
                )
        
        # No matching peer found
        print(f"[INFO] No peer found matching target IP: {target_ip}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
        
    except SystemExit:
        # API request failed, return not found status
        print(f"[ERROR] Failed to query peers from {base_url}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)
    except KeyError as e:
        print(f"[ERROR] Missing expected field: {e}", file=sys.stderr)
        return Status(found=False, active_appliance=0, primary_ip="", secondary_ip="", id=0)


def determine_state(
    peer_ip: str,
    hsa_ip: str,
    spare_ip: str,
    status_peer: Status,
    status_hsa: Status,
    status_spare: Status
) -> int:
    """
    Determine the cluster state based on the peer information from all three nodes.
    
    State table:
    | State | active_appliance | primary_ip | secondary_ip | not_found      |
    | ----- | ---------------- | ---------- | ------------ | -------------- |
    | 1     | 1                | peer       | hsa          | spare          |
    | 2     | 2                | peer       | hsa          | spare          |
    | 3     | 1                | hsa        | peer         | spare          |
    | 4     | 1                | hsa        | empty        | spare and peer |
    | 5     | 1                | hsa        | spare        | peer           |
    | 6     | 2                | hsa        | spare        | peer           |
    | 7     | 1                | spare      | hsa          | peer           |
    | 8     | 1                | peer       | empty        | spare and hsa  |
    
    Args:
        peer_ip: IP address of the peer node
        hsa_ip: IP address of the HSA node
        spare_ip: IP address of the spare node
        status_peer: Status from querying the peer node
        status_hsa: Status from querying the HSA node
        status_spare: Status from querying the spare node
        
    Returns:
        Integer state (1-8), or 0 if no match
    """
    print("\n[DEBUG] Determining state...", file=sys.stderr)
    print(f"[DEBUG] Peer status: found={status_peer.found}, active={status_peer.active_appliance}, primary={status_peer.primary_ip}, secondary={status_peer.secondary_ip}", file=sys.stderr)
    print(f"[DEBUG] HSA status: found={status_hsa.found}, active={status_hsa.active_appliance}, primary={status_hsa.primary_ip}, secondary={status_hsa.secondary_ip}", file=sys.stderr)
    print(f"[DEBUG] Spare status: found={status_spare.found}, active={status_spare.active_appliance}, primary={status_spare.primary_ip}, secondary={status_spare.secondary_ip}", file=sys.stderr)
    
    # Use the first found status to get the cluster configuration
    # All three should return the same cluster info if they're all accessible
    cluster_status = None
    if status_peer.found:
        cluster_status = status_peer
    elif status_hsa.found:
        cluster_status = status_hsa
    elif status_spare.found:
        cluster_status = status_spare
    
    if cluster_status is None:
        print("[ERROR] No peer information found from any node", file=sys.stderr)
        return 0
    
    active_appliance = cluster_status.active_appliance
    primary_ip = cluster_status.primary_ip
    secondary_ip = cluster_status.secondary_ip
    
    # Determine which nodes are not found
    not_found = []
    if not status_peer.found:
        not_found.append("peer")
    if not status_hsa.found:
        not_found.append("hsa")
    if not status_spare.found:
        not_found.append("spare")
    
    print(f"[DEBUG] Active appliance: {active_appliance}", file=sys.stderr)
    print(f"[DEBUG] Primary IP: {primary_ip}", file=sys.stderr)
    print(f"[DEBUG] Secondary IP: {secondary_ip}", file=sys.stderr)
    print(f"[DEBUG] Not found: {not_found}", file=sys.stderr)
    
    # State 1: active=1, primary=peer, secondary=hsa, not_found=spare
    if (active_appliance == 1 and 
        primary_ip == peer_ip and 
        secondary_ip == hsa_ip and 
        not_found == ["spare"]):
        return 1
    
    # State 2: active=2, primary=peer, secondary=hsa, not_found=spare
    if (active_appliance == 2 and 
        primary_ip == peer_ip and 
        secondary_ip == hsa_ip and 
        not_found == ["spare"]):
        return 2
    
    # State 3: active=1, primary=hsa, secondary=peer, not_found=spare
    if (active_appliance == 1 and 
        primary_ip == hsa_ip and 
        secondary_ip == peer_ip and 
        not_found == ["spare"]):
        return 3
    
    # State 4: active=1, primary=hsa, secondary=empty, not_found=spare and peer
    if (active_appliance == 1 and 
        primary_ip == hsa_ip and 
        secondary_ip == "" and 
        set(not_found) == {"spare", "peer"}):
        return 4
    
    # State 5: active=1, primary=hsa, secondary=spare, not_found=peer
    if (active_appliance == 1 and 
        primary_ip == hsa_ip and 
        secondary_ip == spare_ip and 
        not_found == ["peer"]):
        return 5
    
    # State 6: active=2, primary=hsa, secondary=spare, not_found=peer
    if (active_appliance == 2 and 
        primary_ip == hsa_ip and 
        secondary_ip == spare_ip and 
        not_found == ["peer"]):
        return 6
    
    # State 7: active=1, primary=spare, secondary=hsa, not_found=peer
    if (active_appliance == 1 and 
        primary_ip == spare_ip and 
        secondary_ip == hsa_ip and 
        not_found == ["peer"]):
        return 7
    
    # State 8: active=1, primary=peer, secondary=empty, not_found=spare and hsa
    if (active_appliance == 1 and 
        primary_ip == peer_ip and 
        secondary_ip == "" and 
        set(not_found) == {"spare", "hsa"}):
        return 8
    
    # No match found
    print("[WARNING] State does not match any known configuration", file=sys.stderr)
    return 0


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting get_state.py script", file=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Determine cluster state by querying peer information from multiple nodes"
    )
    parser.add_argument(
        "--token_peer",
        required=True,
        help="Bearer token for peer node authentication"
    )
    parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of peer node"
    )
    parser.add_argument(
        "--port_peer",
        required=True,
        type=int,
        help="Port number for peer node"
    )
    parser.add_argument(
        "--token_hsa",
        required=True,
        help="Bearer token for HSA node authentication"
    )
    parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of HSA node"
    )
    parser.add_argument(
        "--port_hsa",
        required=True,
        type=int,
        help="Port number for HSA node"
    )
    parser.add_argument(
        "--token_spare",
        required=True,
        help="Bearer token for spare node authentication"
    )
    parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of spare node"
    )
    parser.add_argument(
        "--port_spare",
        required=True,
        type=int,
        help="Port number for spare node"
    )
    
    args = parser.parse_args()
    
    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Peer - IP: {args.ip_peer}, Port: {args.port_peer}", file=sys.stderr)
    print(f"[DEBUG]   HSA - IP: {args.ip_hsa}, Port: {args.port_hsa}", file=sys.stderr)
    print(f"[DEBUG]   Spare - IP: {args.ip_spare}, Port: {args.port_spare}", file=sys.stderr)
    
    # Create Node objects
    node_peer = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    node_hsa = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)
    node_spare = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)
    
    print("=" * 60, file=sys.stderr)
    print("Cluster State Determination", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Query peer information from all three nodes
    print("\n[INFO] Querying peer node...", file=sys.stderr)
    status_peer = get_peer_info(node_peer, args.ip_peer)
    
    print("\n[INFO] Querying HSA node...", file=sys.stderr)
    status_hsa = get_peer_info(node_hsa, args.ip_hsa)
    
    print("\n[INFO] Querying spare node...", file=sys.stderr)
    status_spare = get_peer_info(node_spare, args.ip_spare)
    
    # Determine the state
    state = determine_state(
        args.ip_peer,
        args.ip_hsa,
        args.ip_spare,
        status_peer,
        status_hsa,
        status_spare
    )
    
    # Get the peer ID from the first found status
    peer_id = 0
    if status_peer.found:
        peer_id = status_peer.id
    elif status_hsa.found:
        peer_id = status_hsa.id
    elif status_spare.found:
        peer_id = status_spare.id
    
    print("\n" + "=" * 60, file=sys.stderr)
    print(f"✓ State determination completed: State {state}, ID {peer_id}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Output the state and ID as JSON
    output = {
        "state": state,
        "id": peer_id
    }
    print(json.dumps(output))
    
    return 0  # Always return 0 for success


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob