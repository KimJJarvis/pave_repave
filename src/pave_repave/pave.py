#!/usr/bin/env python3
"""
Script to query peer information, get tokens, or perform fail-over from NMS API.
Supports multiple commands: peer_info, get_token, get_integration_token, and fail_over.
"""

import argparse
import sys
import json
import logging

from pave_repave.node import Node
from pave_repave.peer_info import peer_info
from pave_repave.utilities import setup_logging
from pave_repave.get_token import get_token, get_authentication_token
from pave_repave.get_integration_token import get_integration_token
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.become_hsa import become_hsa
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.add_hsa import add_hsa
from pave_repave.remove_hsa import remove_hsa
from pave_repave.state_info import state_info, str_state
from pave_repave.paverepave import paverepave
from pave_repave.config import config

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the script."""
    # Create parent parser with common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--log-level",
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parent_parser.add_argument(
        "--log-file", type=str, default=None, help="Log to file instead of console"
    )
    parent_parser.add_argument(
        "--username", required=True, help="Username for authentication"
    )
    parent_parser.add_argument(
        "--password", required=True, help="Password for authentication"
    )
    parent_parser.add_argument(
        "--port_forward",
        action="store_true",
        help="Enable port forwarding (sets config.port_forward to True)"
    )
    
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Query peer information, get tokens, or perform fail-over from NMS API."
    )
    
    # Create subparsers for each command
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Command to execute"
    )
    
    # peer_info subcommand
    peer_info_parser = subparsers.add_parser(
        "peer_info",
        parents=[parent_parser],
        help="Query peer information"
    )
    peer_info_parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the node (in dot format)"
    )
    peer_info_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number of the node"
    )
    
    # get_token subcommand
    get_token_parser = subparsers.add_parser(
        "get_token",
        parents=[parent_parser],
        help="Retrieve authentication token"
    )
    get_token_parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the node (in dot format)"
    )
    get_token_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number of the node"
    )
    
    # get_integration_token subcommand
    get_integration_token_parser = subparsers.add_parser(
        "get_integration_token",
        parents=[parent_parser],
        help="Retrieve integration token"
    )
    get_integration_token_parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the node (in dot format)"
    )
    get_integration_token_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number of the node"
    )
    
    # fail_over subcommand
    fail_over_parser = subparsers.add_parser(
        "fail_over",
        parents=[parent_parser],
        help="Perform fail-over operation"
    )
    fail_over_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer (dot format)"
    )
    fail_over_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer"
    )
    
    # switch_primary_secondary subcommand
    switch_primary_secondary_parser = subparsers.add_parser(
        "switch_primary_secondary",
        parents=[parent_parser],
        help="Switch primary and secondary appliance roles on a peer"
    )
    switch_primary_secondary_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer (dot format)"
    )
    switch_primary_secondary_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer"
    )
    switch_primary_secondary_parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID of the peer in the peers table"
    )
    
    # become_hsa subcommand
    become_hsa_parser = subparsers.add_parser(
        "become_hsa",
        parents=[parent_parser],
        help="Make a spare node become an HSA"
    )
    become_hsa_parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the spare node (dot format)"
    )
    become_hsa_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number of the spare node"
    )
    become_hsa_parser.add_argument(
        "--ip_peer",
        required=True,
        help="Primary/Peer IP address in the cluster (dot format)"
    )
    become_hsa_parser.add_argument(
        "--integration_token",
        required=True,
        help="Integration token"
    )
    
    # leave_cluster_hsa subcommand
    leave_cluster_hsa_parser = subparsers.add_parser(
        "leave_cluster_hsa",
        parents=[parent_parser],
        help="Make an HSA node leave the cluster"
    )
    leave_cluster_hsa_parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the HSA (dot format)"
    )
    leave_cluster_hsa_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number of the HSA"
    )
    leave_cluster_hsa_parser.add_argument(
        "--integration_token",
        required=True,
        help="Integration token"
    )
    
    # add_hsa subcommand
    add_hsa_parser = subparsers.add_parser(
        "add_hsa",
        parents=[parent_parser],
        help="Add an HSA to a cluster"
    )
    add_hsa_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer HSA node (dot format)"
    )
    add_hsa_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer HSA node"
    )
    add_hsa_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node (dot format)"
    )
    add_hsa_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node"
    )
    add_hsa_parser.add_argument(
        "--new_cluster",
        action="store_true",
        help="Create a new cluster (validates that both peer and spare are not in any cluster)"
    )
    
    # remove_hsa subcommand
    remove_hsa_parser = subparsers.add_parser(
        "remove_hsa",
        parents=[parent_parser],
        help="Remove an HSA from a cluster"
    )
    remove_hsa_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    remove_hsa_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node"
    )
    remove_hsa_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA to be removed (dot format)"
    )
    remove_hsa_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number of the HSA to be removed"
    )
    
    # state_info subcommand
    state_info_parser = subparsers.add_parser(
        "state_info",
        parents=[parent_parser],
        help="Determine the current state of the peer/HSA cluster"
    )
    state_info_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    state_info_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    state_info_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    state_info_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    state_info_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node"
    )
    state_info_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number for spare node"
    )
    
    # pave_repave subcommand
    pave_repave_parser = subparsers.add_parser(
        "pave_repave",
        parents=[parent_parser],
        help="Perform pave/repave operation on the cluster"
    )
    pave_repave_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    pave_repave_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    pave_repave_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    pave_repave_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    pave_repave_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node"
    )
    pave_repave_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number for spare node"
    )

    args = parser.parse_args()

    # Set port_forward in config if specified
    if args.port_forward:
        config.port_forward = True
        logger.debug("Port forwarding enabled via --port_forward flag")
    
    # ⚠️ Must be called before any other logging calls
    setup_logging(args.log_level, args.log_file)

    try:
        if args.command == "peer_info":
            # Get authentication token
            token = get_authentication_token(username=args.username, password=args.password, ip=args.ip, port=args.port)
            
            # Create Node object
            node = Node(port=args.port, token=token, ip=args.ip)

            # Get peer info
            status = peer_info(node=node)

            # Print parsed status to console (stdout)
            if status is None:
                print("Not a peer or HSA")
            else:
                parsed_status = json.dumps(
                    {
                        "active_appliance": status.active_appliance,
                        "primary_ip": status.primary_ip,
                        "secondary_ip": status.secondary_ip,
                        "id": status.id,
                    },
                    indent=2,
                )
                print("Parsed Peer Info Status:")
                print(parsed_status)
        
        elif args.command == "get_token":
            # Get authentication token
            token = get_authentication_token(username=args.username, password=args.password, ip=args.ip, port=args.port)
            
            # Output the authentication token to stdout
            print(token)
        
        elif args.command == "get_integration_token":
            # Get authentication token
            token = get_authentication_token(username=args.username, password=args.password, ip=args.ip, port=args.port)

            # Create Node object with IP
            node = Node(port=args.port, token=token, ip=args.ip)
            
            # Get integration token
            integration_token = get_integration_token(node=node)
            
            # Output the integration token to stdout
            print(integration_token)
        
        elif args.command == "fail_over":
            # Get authentication token using port_peer
            token = get_authentication_token(username=args.username, password=args.password, ip=args.ip_peer, port=args.port_peer)
            
            # Create Node object with peer IP and port
            node = Node(port=args.port_peer, token=token, ip=args.ip_peer)
            
            # Call fail-over
            fail_over(node=node)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "switch_primary_secondary":
            # Get authentication token
            token = get_token(username=args.username, password=args.password, port=args.port_peer)
            
            # Create Node object
            node = Node(port=args.port_peer, token=token, ip=args.ip_peer)
            
            # Call switch-primary-secondary
            switch_primary_secondary(node=node, id=args.id)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "become_hsa":
            # Get authentication token
            token = get_token(username=args.username, password=args.password, port=args.port)
            
            # Create Node object
            node = Node(port=args.port, token=token, ip=args.ip)
            
            # Call become-hsa
            response = become_hsa(node=node, ip_peer=args.ip_peer, integration_token=args.integration_token)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "leave_cluster_hsa":
            # Get authentication token
            token = get_token(username=args.username, password=args.password, port=args.port)
            
            # Create Node object
            node = Node(port=args.port, token=token, ip=args.ip)
            
            # Call leave-cluster-hsa
            leave_cluster_hsa(node=node, integration_token=args.integration_token)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "add_hsa":
            # Get authentication token for peer node
            peer_token = get_token(username=args.username, password=args.password, port=args.port_peer)
            
            # Get authentication token for spare node
            spare_token = get_token(username=args.username, password=args.password, port=args.port_spare)
            
            # Create Node objects
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)
            
            # Call add_hsa
            add_hsa(peer=peer_node, spare=spare_node, new_cluster=args.new_cluster)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "remove_hsa":
            # Get authentication token for peer node
            peer_token = get_token(username=args.username, password=args.password, port=args.port_peer)
            
            # Get authentication token for HSA node
            hsa_token = get_token(username=args.username, password=args.password, port=args.port_hsa)
            
            # Create Node objects
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            hsa_node = Node(port=args.port_hsa, token=hsa_token, ip=args.ip_hsa)
            
            # Call remove_hsa
            remove_hsa(peer=peer_node, hsa=hsa_node)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "state_info":
            # Get authentication tokens for each node
            token_peer = get_token(username=args.username, password=args.password, port=args.port_peer)
            token_hsa = get_token(username=args.username, password=args.password, port=args.port_hsa)
            token_spare = get_token(username=args.username, password=args.password, port=args.port_spare)
            
            # Construct Node objects
            peer_node = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa_node = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare_node = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)
            
            # Determine the current state first
            current_state = state_info(peer=peer_node, hsa=hsa_node, spare=spare_node)
            
            # Print the state table with state information
            print(str_state(peer=peer_node, hsa=hsa_node, spare=spare_node, state=current_state))
            print()
            
            # Print state to console (stdout)
            print(f"State: {current_state}")
        
        elif args.command == "pave_repave":
            # Get authentication tokens for each node
            token_peer = get_token(username=args.username, password=args.password, port=args.port_peer)
            token_hsa = get_token(username=args.username, password=args.password, port=args.port_hsa)
            token_spare = get_token(username=args.username, password=args.password, port=args.port_spare)
            
            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)
            
            # Call paverepave
            paverepave(peer=peer, hsa=hsa, spare=spare)
            
            print("✓ SUCCESS: Pave/Repave completed successfully!")
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"✗ Operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"✗ Operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Operation failed with unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
