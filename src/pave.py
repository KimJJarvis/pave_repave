#!/usr/bin/env python3
"""
Fused workflow script that orchestrates fail-over, switch-primary-secondary,
get-integration-token, and leave-cluster-hsa operations.
"""

import argparse
import sys
import time

from node import Node
from fail_over import fail_over
from switch_primary_secondary import switch_primary_secondary
from get_integration_token import get_integration_token
from get_peer_info import get_peer_info
from peer_info import get_peer_info as get_peer_info_v3
from leave_cluster_hsa import leave_cluster_hsa
from utilities import (
    validate_ip_address,
    validate_port,
    validate_token_length,
    exit_with_error
)


def verify_peer_info(node: Node, node_ip: str, hsa_ip: str, node_name: str):
    """
    Verify peer information on a node.
    
    Args:
        node: Node object to query
        node_ip: Expected primary IP address
        hsa_ip: Expected secondary IP address
        node_name: Name of the node being verified (for logging)
    """
    print(f"\n[{node_name}] Verifying peer information...", file=sys.stderr)
    
    # Call get_peer_info with node_ip
    print(f"[{node_name}] Checking node IP {node_ip}...", file=sys.stderr)
    node_check = Node(port=node.port, token=node.token, ip=node_ip)
    node_status, _ = get_peer_info_v3(node_check)
    
    if not node_status.found:
        exit_with_error(f"[{node_name}] Node {node_ip} not found in peer info")
    
    if node_status.primary_ip != node_ip:
        exit_with_error(f"[{node_name}] Node IP {node_ip} is not a primaryIp (found: {node_status.primary_ip})")
    
    print(f"✓ [{node_name}] Node {node_ip} verified as primaryIp", file=sys.stderr)
    
    # Call get_peer_info with hsa_ip
    print(f"[{node_name}] Checking HSA IP {hsa_ip}...", file=sys.stderr)
    hsa_check = Node(port=node.port, token=node.token, ip=hsa_ip)
    hsa_status, _ = get_peer_info_v3(hsa_check)
    
    if not hsa_status.found:
        exit_with_error(f"[{node_name}] HSA {hsa_ip} not found in peer info")
    
    if hsa_status.secondary_ip != hsa_ip:
        exit_with_error(f"[{node_name}] HSA IP {hsa_ip} is not a secondaryIp (found: {hsa_status.secondary_ip})")
    
    if hsa_status.active_appliance != 1:  # 1 = PRIMARY
        exit_with_error(f"[{node_name}] activeAppliance is not PRIMARY (found: {hsa_status.active_appliance})")
    
    print(f"✓ [{node_name}] HSA {hsa_ip} verified as secondaryIp with activeAppliance=PRIMARY", file=sys.stderr)
    print(f"✓ [{node_name}] Peer information verification complete", file=sys.stderr)


def main():
    """Main entry point for the fused workflow script."""
    print("[DEBUG] Starting fused.py script", file=sys.stderr)
    
    parser = argparse.ArgumentParser(
        description="Fused workflow for fail-over and cluster operations"
    )
    parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node"
    )
    parser.add_argument(
        "--token_peer",
        required=True,
        help="Bearer token for peer authentication"
    )
    parser.add_argument(
        "--port_peer",
        required=True,
        type=int,
        help="Port number for peer node"
    )
    parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node"
    )
    parser.add_argument(
        "--port_hsa",
        required=True,
        type=int,
        help="Port number for HSA node"
    )
    
    args = parser.parse_args()
    
    print(f"[DEBUG] Arguments parsed:", file=sys.stderr)
    print(f"[DEBUG]   Peer IP: {args.ip_peer}", file=sys.stderr)
    print(f"[DEBUG]   Peer Token: {args.token_peer[:20]}...", file=sys.stderr)
    print(f"[DEBUG]   Peer Port: {args.port_peer}", file=sys.stderr)
    print(f"[DEBUG]   HSA IP: {args.ip_hsa}", file=sys.stderr)
    print(f"[DEBUG]   HSA Port: {args.port_hsa}", file=sys.stderr)

    # Step 0: Verify parameters
    print("\n[STEP 1] Verifying parameters...", file=sys.stderr)

    # Validate IP addresses
    if not validate_ip_address(args.ip_peer):
        exit_with_error(f"Invalid peer IP address: {args.ip_peer}")
    
    if not validate_ip_address(args.ip_hsa):
        exit_with_error(f"Invalid HSA IP address: {args.ip_hsa}")
    
    # Verify IPs are distinct
    if args.ip_peer == args.ip_hsa:
        exit_with_error(f"Peer and HSA IP addresses must be distinct: {args.ip_peer}")
    
    # Validate port numbers
    if not validate_port(args.port_peer):
        exit_with_error(f"Invalid peer port number: {args.port_peer} (must be 0-65535)")
    
    if not validate_port(args.port_hsa):
        exit_with_error(f"Invalid HSA port number: {args.port_hsa} (must be 0-65535)")
    
    # Verify ports are distinct
    if args.port_peer == args.port_hsa:
        exit_with_error(f"Peer and HSA port numbers must be distinct: {args.port_peer}")
    
    # Validate token length
    if not validate_token_length(args.token_peer, 361):
        exit_with_error(f"Invalid peer token length: {len(args.token_peer)} (expected 361)")
    
    print("✓ All validations passed", file=sys.stderr)
    
    # Construct Node objects
    peer_node = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa_node = Node(port=args.port_hsa, token=args.token_peer, ip=args.ip_hsa)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("Fused Workflow", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Peer Node: https://localhost:{peer_node.port} (forwarded to {peer_node.ip})", file=sys.stderr)
    print(f"HSA Node: https://localhost:{hsa_node.port} (forwarded to {hsa_node.ip})", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Step 1: Verify peer information on the peer
    print("\n[STEP 1] Verifying peer information on peer...", file=sys.stderr)
    verify_peer_info(peer_node, args.ip_peer, args.ip_hsa, "PEER")
    print("✓ Step 1 completed successfully", file=sys.stderr)
    
    # Step 2: Verify peer information on the HSA
    print("\n[STEP 2] Verifying peer information on HSA...", file=sys.stderr)
    verify_peer_info(hsa_node, args.ip_peer, args.ip_hsa, "HSA")
    print("✓ Step 2 completed successfully", file=sys.stderr)
    
    # Step 3: Call fail_over() on the peer
    print("\n[STEP 3] Calling fail_over on peer...", file=sys.stderr)
    fail_over_response = fail_over(peer_node)
    
    if fail_over_response.code == 400:
        exit_with_error(f"fail_over returned 400: {fail_over_response.message}")
    
    if "LeaderFollower Job Active, cannot Fail-Over" in fail_over_response.message:
        exit_with_error(f"fail_over error: {fail_over_response.message}")
    
    if "Failover successfully started" not in fail_over_response.message:
        exit_with_error(f"Unexpected fail_over response: {fail_over_response.message}")
    
    print("✓ fail_over completed successfully", file=sys.stderr)
    
    # Step 4: Get peer info to obtain peer ID
    print("\n[STEP 4] Getting peer info to obtain peer ID...", file=sys.stderr)
    peer_status = get_peer_info(peer_node)
    
    if not peer_status.found:
        exit_with_error("Could not find peer information")
    
    peer_id = peer_status.id
    print(f"✓ Peer ID obtained: {peer_id}", file=sys.stderr)
    
    # Step 5: Call switch_primary_secondary() on the peer
    print("\n[STEP 5] Calling switch_primary_secondary on peer...", file=sys.stderr)
    
    while True:
        switch_response = switch_primary_secondary(peer_node, peer_id)        
        
        # Check for LeaderFollower Job Active 
        if "LeaderFollower Job Active, cannot switch-primary-secondary" in switch_response.message:
            print("⚠ LeaderFollower Job Active, waiting 30 seconds before retry...", file=sys.stderr)
            time.sleep(30)
            continue

        # Check for fail over not yet complete 
        if "A secondary-leader appliance was not found on this peer" in switch_response.message:
            print("⚠ Fail over not yet complete, waiting 30 seconds before retry...", file=sys.stderr)
            time.sleep(30)
            continue

        # Now check for other 400 errors
        if switch_response.code == 400:
            exit_with_error(f"switch_primary_secondary returned 400: {switch_response.message}")
        
        # Check for success
        if "The primary / secondary appliance roles on this peer have been switched" in switch_response.message:
            print("✓ switch_primary_secondary completed successfully", file=sys.stderr)
            break
        
        # Any other response is an error
        exit_with_error(f"Unexpected switch_primary_secondary response: {switch_response.message}")
    
    # Step 6: Get integration token from the peer
    print("\n[STEP 6] Getting integration token from peer...", file=sys.stderr)
    integration_token = get_integration_token(hsa_node)
      
    print(f"✓ Integration token obtained (length: {len(integration_token)})", file=sys.stderr)
    
    # Step 7: Call leave_cluster_hsa from the HSA
    print("\n[STEP 7] Calling leave_cluster_hsa on HSA...", file=sys.stderr)
    try:
        leave_cluster_hsa(peer_node, integration_token)
        print("✓ leave_cluster_hsa completed successfully", file=sys.stderr)
    except Exception as e:
        exit_with_error(f"leave_cluster_hsa failed: {str(e)}")
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Fused workflow completed successfully!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob