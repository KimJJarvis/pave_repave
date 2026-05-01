#!/usr/bin/env python3
"""
Script to replace a node in a cluster.
Orchestrates the complete workflow to replace a peer node with a spare node.
"""

import argparse
import sys
import re
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from node import Node
from status import Status
from get_peer_info import get_peer_info
from get_integration_token import get_integration_token
from fail_over import fail_over
from switch_primary_secondary import switch_primary_secondary
from leave_cluster_hsa import leave_cluster_hsa
from become_hsa import become_hsa


def validate_ip_address(ip: str) -> bool:
    """
    Validate that the IP address is a string with dots (e.g., "9.24.143.26").
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check if it's a string with dots and valid IP format
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    # Validate each octet is 0-255
    octets = ip.split('.')
    for octet in octets:
        if int(octet) > 255:
            return False
    
    return True


def validate_port(port: int) -> bool:
    """
    Validate that the port is a valid integer in the range 0-65535.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= port <= 65535


def validate_bearer_token(token: str) -> bool:
    """
    Validate that the bearer token is a string with length of 362 characters.
    
    Args:
        token: Bearer token to validate
        
    Returns:
        True if valid, False otherwise
    """
    return len(token) == 362


def validate_integration_token(token: str) -> bool:
    """
    Validate that the integration token is a string with length of 273 characters.
    
    Args:
        token: Integration token to validate
        
    Returns:
        True if valid, False otherwise
    """
    return len(token) == 273


def main():
    """Main entry point for the script."""
    print("[DEBUG] Starting replace-node.py script", file=sys.stderr)
    
    parser = argparse.ArgumentParser(
        description="Replace a peer node with a spare node in a cluster"
    )
    
    # Peer node arguments
    parser.add_argument(
        "--ip_peer",
        required=True,
        help="Peer IP address (dot format, e.g., 9.24.143.26)"
    )
    parser.add_argument(
        "--token_peer",
        required=True,
        help="Peer bearer token (362 characters)"
    )
    parser.add_argument(
        "--port_peer",
        required=True,
        type=int,
        help="Peer localhost port (0-65535)"
    )
    
    # HSA node arguments
    parser.add_argument(
        "--ip_hsa",
        required=True,
        help="HSA IP address (dot format, e.g., 9.24.143.26)"
    )
    parser.add_argument(
        "--token_hsa",
        required=True,
        help="HSA bearer token (362 characters)"
    )
    parser.add_argument(
        "--port_hsa",
        required=True,
        type=int,
        help="HSA localhost port (0-65535)"
    )
    
    # Spare node arguments
    parser.add_argument(
        "--ip_spare",
        required=True,
        help="Spare IP address (dot format, e.g., 9.24.143.26)"
    )
    parser.add_argument(
        "--token_spare",
        required=True,
        help="Spare bearer token (362 characters)"
    )
    parser.add_argument(
        "--port_spare",
        required=True,
        type=int,
        help="Spare localhost port (0-65535)"
    )
    
    args = parser.parse_args()
    
    # Validate IP addresses
    print("\n[Validation] Validating IP addresses...", file=sys.stderr)
    if not validate_ip_address(args.ip_peer):
        print(f"[ERROR] Invalid peer IP address: {args.ip_peer}", file=sys.stderr)
        sys.exit(1)
    if not validate_ip_address(args.ip_hsa):
        print(f"[ERROR] Invalid HSA IP address: {args.ip_hsa}", file=sys.stderr)
        sys.exit(1)
    if not validate_ip_address(args.ip_spare):
        print(f"[ERROR] Invalid spare IP address: {args.ip_spare}", file=sys.stderr)
        sys.exit(1)
    print("✓ All IP addresses are valid", file=sys.stderr)
    
    # Validate ports
    print("\n[Validation] Validating ports...", file=sys.stderr)
    if not validate_port(args.port_peer):
        print(f"[ERROR] Invalid peer port: {args.port_peer}", file=sys.stderr)
        sys.exit(1)
    if not validate_port(args.port_hsa):
        print(f"[ERROR] Invalid HSA port: {args.port_hsa}", file=sys.stderr)
        sys.exit(1)
    if not validate_port(args.port_spare):
        print(f"[ERROR] Invalid spare port: {args.port_spare}", file=sys.stderr)
        sys.exit(1)
    print("✓ All ports are valid", file=sys.stderr)
    
    # Validate bearer tokens
    print("\n[Validation] Validating bearer tokens...", file=sys.stderr)
    if not validate_bearer_token(args.token_peer):
        print(f"[ERROR] Invalid peer bearer token length: {len(args.token_peer)} (expected 362)", file=sys.stderr)
        sys.exit(1)
    if not validate_bearer_token(args.token_hsa):
        print(f"[ERROR] Invalid HSA bearer token length: {len(args.token_hsa)} (expected 362)", file=sys.stderr)
        sys.exit(1)
    if not validate_bearer_token(args.token_spare):
        print(f"[ERROR] Invalid spare bearer token length: {len(args.token_spare)} (expected 362)", file=sys.stderr)
        sys.exit(1)
    print("✓ All bearer tokens are valid", file=sys.stderr)
    
    # Create Node objects
    peer = Node(port=args.port_peer, token=args.token_peer, ip=args.ip_peer)
    hsa = Node(port=args.port_hsa, token=args.token_hsa, ip=args.ip_hsa)
    spare = Node(port=args.port_spare, token=args.token_spare, ip=args.ip_spare)
    
    print("\n" + "=" * 80, file=sys.stderr)
    print("REPLACE NODE WORKFLOW", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"Peer:  {peer.ip}:{peer.port}", file=sys.stderr)
    print(f"HSA:   {hsa.ip}:{hsa.port}", file=sys.stderr)
    print(f"Spare: {spare.ip}:{spare.port}", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    
    # Step 1: Verify peer is found
    print("\n[Step 1] Verify peer is found...", file=sys.stderr)
    peer_status = get_peer_info(peer)
    if not peer_status.found:
        print(f"[ERROR] Peer not found!", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Peer is found", file=sys.stderr)
    
    # Step 2: Verify peer active_appliance == 1
    print("\n[Step 2] Verify peer active_appliance == 1...", file=sys.stderr)
    if peer_status.active_appliance != 1:
        print(f"[ERROR] Peer active_appliance is {peer_status.active_appliance}, expected 1", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Peer active_appliance is 1", file=sys.stderr)
    
    # Step 3: Verify peer.id == hsa.id
    print("\n[Step 3] Verify peer.id == hsa.id...", file=sys.stderr)
    hsa_status = get_peer_info(hsa)
    if peer_status.id != hsa_status.id:
        print(f"[ERROR] Peer ID ({peer_status.id}) != HSA ID ({hsa_status.id})", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Peer ID matches HSA ID: {peer_status.id}", file=sys.stderr)
    
    # Step 4: Verify spare is not found
    print("\n[Step 4] Verify spare is not found...", file=sys.stderr)
    spare_status = get_peer_info(spare)
    if spare_status.found:
        print(f"[ERROR] Spare is already found in cluster!", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Spare is not found (as expected)", file=sys.stderr)
    
    # Step 5: Set id variable
    print("\n[Step 5] Set id variable...", file=sys.stderr)
    id = peer_status.id
    print(f"✓ ID set to: {id}", file=sys.stderr)
    
    # Step 6: Fail over peer
    print("\n[Step 6] Fail over peer...", file=sys.stderr)
    fail_over(node=peer)
    print(f"✓ Fail over completed", file=sys.stderr)
    
    # Step 7: Switch primary/secondary on HSA
    print("\n[Step 7] Switch primary/secondary on HSA...", file=sys.stderr)
    switch_primary_secondary(node=hsa, id=id)
    print(f"✓ Switch primary/secondary completed", file=sys.stderr)
    
    # Step 8: Get integration token from HSA
    print("\n[Step 8] Get integration token from HSA...", file=sys.stderr)
    integration_token = get_integration_token(node=hsa)
    if not validate_integration_token(integration_token):
        print(f"[WARNING] Integration token length is {len(integration_token)}, expected 273", file=sys.stderr)
    print(f"✓ Integration token retrieved (length: {len(integration_token)})", file=sys.stderr)
    
    # Step 9: Leave cluster HSA (peer)
    print("\n[Step 9] Leave cluster HSA (peer)...", file=sys.stderr)
    leave_cluster_hsa(node=peer, integration_token=integration_token)
    print(f"✓ Peer left cluster", file=sys.stderr)
    
    # Step 10: Get integration token from HSA (again)
    print("\n[Step 10] Get integration token from HSA (again)...", file=sys.stderr)
    integration_token = get_integration_token(node=hsa)
    if not validate_integration_token(integration_token):
        print(f"[WARNING] Integration token length is {len(integration_token)}, expected 273", file=sys.stderr)
    print(f"✓ Integration token retrieved (length: {len(integration_token)})", file=sys.stderr)
    
    # Step 11: Become HSA (spare)
    print("\n[Step 11] Become HSA (spare)...", file=sys.stderr)
    become_hsa(node=spare, ip_cluster=hsa.ip, integration_token=integration_token)
    print(f"✓ Spare became HSA", file=sys.stderr)
    
    # Step 12: Fail over HSA
    print("\n[Step 12] Fail over HSA...", file=sys.stderr)
    fail_over(node=hsa)
    print(f"✓ HSA fail over completed", file=sys.stderr)
    
    # Step 13: Switch primary/secondary on spare
    print("\n[Step 13] Switch primary/secondary on spare...", file=sys.stderr)
    switch_primary_secondary(node=spare, id=id)
    print(f"✓ Switch primary/secondary on spare completed", file=sys.stderr)
    
    # Step 14: Verify spare is found
    print("\n[Step 14] Verify spare is found...", file=sys.stderr)
    spare_status = get_peer_info(spare)
    if not spare_status.found:
        print(f"[ERROR] Spare not found after becoming HSA!", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Spare is found", file=sys.stderr)
    
    # Step 15: Verify spare active_appliance == 1
    print("\n[Step 15] Verify spare active_appliance == 1...", file=sys.stderr)
    if spare_status.active_appliance != 1:
        print(f"[ERROR] Spare active_appliance is {spare_status.active_appliance}, expected 1", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Spare active_appliance is 1", file=sys.stderr)
    
    # Step 16: Verify spare.id == hsa.id
    print("\n[Step 16] Verify spare.id == hsa.id...", file=sys.stderr)
    hsa_status = get_peer_info(hsa)
    if spare_status.id != hsa_status.id:
        print(f"[ERROR] Spare ID ({spare_status.id}) != HSA ID ({hsa_status.id})", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Spare ID matches HSA ID: {spare_status.id}", file=sys.stderr)
    
    # Step 17: Verify peer is not found
    print("\n[Step 17] Verify peer is not found...", file=sys.stderr)
    peer_status = get_peer_info(peer)
    if peer_status.found:
        print(f"[ERROR] Peer is still found in cluster!", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Peer is not found (as expected)", file=sys.stderr)
    
    print("\n" + "=" * 80, file=sys.stderr)
    print("✓ ALL STEPS COMPLETED SUCCESSFULLY!", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"\nNode replacement complete:", file=sys.stderr)
    print(f"  - Peer ({peer.ip}) has been removed from the cluster", file=sys.stderr)
    print(f"  - Spare ({spare.ip}) has replaced the peer in the cluster", file=sys.stderr)
    print(f"  - HSA ({hsa.ip}) remains in the cluster", file=sys.stderr)


if __name__ == "__main__":
    main()

# Made with Bob