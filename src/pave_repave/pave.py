#!/usr/bin/env python3
"""
Script to query peer information, get tokens, or perform fail-over from NMS API.
Supports multiple commands: peer_info, get_token, get_integration_token, and fail_over.
"""

import argparse
import sys
import json
import logging
import os

from pave_repave.node import Node
from pave_repave.peer_info import peer_info
from pave_repave.utilities import setup_logging
from pave_repave.get_token import get_token, get_authentication_token
from pave_repave.get_integration_token import get_integration_token
from pave_repave.fail_over import fail_over
from pave_repave.switch_primary_secondary import switch_primary_secondary
from pave_repave.become_hsa import become_hsa
from pave_repave.leave_cluster_hsa import leave_cluster_hsa
from pave_repave.join_cluster import join_cluster
from pave_repave.leave_cluster import leave_cluster
from pave_repave.remove_peer import remove_peer
from pave_repave.add_hsa import add_hsa, add_new_hsa
from pave_repave.remove_hsa import remove_hsa
from pave_repave.state_info import get_state3, state3_table, get_state2, state2_table, precondition2, postcondition2, get_state1, state1_table, precondition1, postcondition1
from pave_repave.paverepave import repaveswitch, repave, switch
from pave_repave.config import config
from pave_repave.add_peer import add_peer, add_new_peer



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
        "--username", required=False, help="Username for authentication (defaults to CLUSTER_CLIENT_USERNAME env var)"
    )
    parent_parser.add_argument(
        "--password", required=False, help="Password for authentication (defaults to CLUSTER_CLIENT_PASSWORD env var)"
    )
    parent_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Override config.host"
    )
    parent_parser.add_argument(
        "--http_502_max_retries",
        type=int,
        default=None,
        help="Override config.http_502_max_retries"
    )
    parent_parser.add_argument(
        "--http_502_retry_delay",
        type=int,
        default=None,
        help="Override config.http_502_retry_delay"
    )
    parent_parser.add_argument(
        "--http_timeout_value",
        type=int,
        default=None,
        help="Override config.http_timeout_value"
    )
    parent_parser.add_argument(
        "--wait_state_max_retries",
        type=int,
        default=None,
        help="Override config.wait_state_max_retries"
    )
    parent_parser.add_argument(
        "--wait_state_initial_delay",
        type=int,
        default=None,
        help="Override config.wait_state_initial_delay"
    )
    parent_parser.add_argument(
        "--wait_state_retry_delay",
        type=int,
        default=None,
        help="Override config.wait_state_retry_delay"
    )
    parent_parser.add_argument(
        "--wait_state_settle_delay",
        type=int,
        default=None,
        help="Override config.wait_state_settle_delay"
    )
    parent_parser.add_argument(
        "--switch_primary_secondary_max_retries",
        type=int,
        default=None,
        help="Override config.switch_primary_secondary_max_retries"
    )
    parent_parser.add_argument(
        "--switch_primary_secondary_retry_delay",
        type=int,
        default=None,
        help="Override config.switch_primary_secondary_retry_delay"
    )
    parent_parser.add_argument(
        "--fail_over_max_retries",
        type=int,
        default=None,
        help="Override config.fail_over_max_retries"
    )
    parent_parser.add_argument(
        "--fail_over_retry_delay",
        type=int,
        default=None,
        help="Override config.fail_over_retry_delay"
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
    
    # join_cluster subcommand
    join_cluster_parser = subparsers.add_parser(
        "join_cluster",
        parents=[parent_parser],
        help="Join a spare node to an existing cluster"
    )
    join_cluster_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node in the cluster (dot format)"
    )
    join_cluster_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node in the cluster"
    )
    join_cluster_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node joining the cluster (dot format)"
    )
    join_cluster_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node joining the cluster"
    )
    join_cluster_parser.add_argument(
        "--name",
        required=True,
        help="Name of the spare node joining the cluster"
    )
    join_cluster_parser.add_argument(
        "--integration_token",
        required=False,
        help="Integration token (if not provided, will be retrieved from peer node)"
    )
    
    # add_peer subcommand
    add_peer_parser = subparsers.add_parser(
        "add_peer",
        parents=[parent_parser],
        help="Add a spare node to an existing cluster"
    )
    add_peer_parser.add_argument(
        "--ip_cluster",
        required=True,
        help="IP address of the cluster node (dot format)"
    )
    add_peer_parser.add_argument(
        "--port_cluster",
        type=int,
        required=True,
        help="Port number of the cluster node"
    )
    add_peer_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node to add to the cluster (dot format)"
    )
    add_peer_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node to add to the cluster"
    )
    add_peer_parser.add_argument(
        "--name",
        required=True,
        help="Name of the spare node to add to the cluster"
    )
    
    # add_new_peer subcommand
    add_new_peer_parser = subparsers.add_parser(
        "add_new_peer",
        parents=[parent_parser],
        help="Add a new peer node to an existing cluster (with validation)"
    )
    add_new_peer_parser.add_argument(
        "--ip_cluster",
        required=True,
        help="IP address of the cluster node (dot format)"
    )
    add_new_peer_parser.add_argument(
        "--port_cluster",
        type=int,
        required=True,
        help="Port number of the cluster node"
    )
    add_new_peer_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node to add to the cluster (dot format)"
    )
    add_new_peer_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node to add to the cluster"
    )
    add_new_peer_parser.add_argument(
        "--name",
        required=True,
        help="Name of the spare node to add to the cluster"
    )
    
    # leave_cluster subcommand
    leave_cluster_parser = subparsers.add_parser(
        "leave_cluster",
        parents=[parent_parser],
        help="Remove a node from the cluster"
    )
    leave_cluster_parser.add_argument(
        "--ip_cluster",
        required=True,
        help="IP address of the cluster node (dot format)"
    )
    leave_cluster_parser.add_argument(
        "--port_cluster",
        type=int,
        required=True,
        help="Port number of the cluster node"
    )
    leave_cluster_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node leaving the cluster (dot format)"
    )
    leave_cluster_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node leaving the cluster"
    )
    leave_cluster_parser.add_argument(
        "--integration_token",
        required=False,
        help="Integration token (if not provided, will be retrieved from cluster node)"
    )
    
    # remove_peer subcommand
    remove_peer_parser = subparsers.add_parser(
        "remove_peer",
        parents=[parent_parser],
        help="Remove a peer node from the cluster (automatically retrieves integration token)"
    )
    remove_peer_parser.add_argument(
        "--ip_cluster",
        required=True,
        help="IP address of the cluster node (dot format)"
    )
    remove_peer_parser.add_argument(
        "--port_cluster",
        type=int,
        required=True,
        help="Port number of the cluster node"
    )
    remove_peer_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node to remove from the cluster (dot format)"
    )
    remove_peer_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer node to remove from the cluster"
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
    
    # add_new_hsa subcommand
    add_new_hsa_parser = subparsers.add_parser(
        "add_new_hsa",
        parents=[parent_parser],
        help="Add an HSA to create a new cluster"
    )
    add_new_hsa_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer HSA node (dot format)"
    )
    add_new_hsa_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number of the peer HSA node"
    )
    add_new_hsa_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node (dot format)"
    )
    add_new_hsa_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number of the spare node"
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
    
    # state1 subcommand
    state1_parser = subparsers.add_parser(
        "state1",
        parents=[parent_parser],
        help="Determine the current state of a single node"
    )
    state1_parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the node (dot format)"
    )
    state1_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number for node"
    )
    
    # state2 subcommand
    state2_parser = subparsers.add_parser(
        "state2",
        parents=[parent_parser],
        help="Determine the current state of the peer/HSA cluster (2-node)"
    )
    state2_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    state2_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    state2_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    state2_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    
    # switch subcommand
    switch_parser = subparsers.add_parser(
        "switch",
        parents=[parent_parser],
        help="Switch primary and secondary roles"
    )
    switch_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    switch_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    switch_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    switch_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    
    # state3 subcommand
    state3_parser = subparsers.add_parser(
        "state3",
        parents=[parent_parser],
        help="Determine the current state of the peer/HSA cluster"
    )
    state3_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    state3_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    state3_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    state3_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    state3_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node"
    )
    state3_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number for spare node"
    )
    
    # repaveswitch subcommand
    repaveswitch_parser = subparsers.add_parser(
        "repaveswitch",
        parents=[parent_parser],
        help="Perform pave/repave operation on the cluster"
    )
    repaveswitch_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    repaveswitch_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    repaveswitch_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    repaveswitch_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    repaveswitch_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node"
    )
    repaveswitch_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number for spare node"
    )
    
    # repave subcommand
    repave_parser = subparsers.add_parser(
        "repave",
        parents=[parent_parser],
        help="Perform repave operation on the cluster"
    )
    repave_parser.add_argument(
        "--ip_peer",
        required=True,
        help="IP address of the peer node (dot format)"
    )
    repave_parser.add_argument(
        "--port_peer",
        type=int,
        required=True,
        help="Port number for peer node"
    )
    repave_parser.add_argument(
        "--ip_hsa",
        required=True,
        help="IP address of the HSA node (dot format)"
    )
    repave_parser.add_argument(
        "--port_hsa",
        type=int,
        required=True,
        help="Port number for HSA node"
    )
    repave_parser.add_argument(
        "--ip_spare",
        required=True,
        help="IP address of the spare node"
    )
    repave_parser.add_argument(
        "--port_spare",
        type=int,
        required=True,
        help="Port number for spare node"
    )

    args = parser.parse_args()

    # Handle username and password from environment variables if not provided
    username = args.username
    password = args.password
    
    if username is None:
        username = os.environ.get('CLUSTER_CLIENT_USERNAME')
        if username is None:
            print("✗ Error: --username not provided and CLUSTER_CLIENT_USERNAME environment variable not set", file=sys.stderr)
            sys.exit(1)
    
    if password is None:
        password = os.environ.get('CLUSTER_CLIENT_PASSWORD')
        if password is None:
            print("✗ Error: --password not provided and CLUSTER_CLIENT_PASSWORD environment variable not set", file=sys.stderr)
            sys.exit(1)

    config_overrides = {
        "host": args.host,
        "http_502_max_retries": args.http_502_max_retries,
        "http_502_retry_delay": args.http_502_retry_delay,
        "http_timeout_value": args.http_timeout_value,
        "wait_state_max_retries": args.wait_state_max_retries,
        "wait_state_initial_delay": args.wait_state_initial_delay,
        "wait_state_retry_delay": args.wait_state_retry_delay,
        "wait_state_settle_delay": args.wait_state_settle_delay,
        "switch_primary_secondary_max_retries": args.switch_primary_secondary_max_retries,
        "switch_primary_secondary_retry_delay": args.switch_primary_secondary_retry_delay,
        "fail_over_max_retries": args.fail_over_max_retries,
        "fail_over_retry_delay": args.fail_over_retry_delay,
        "log_level": args.log_level,
        "log_file": args.log_file,
    }

    for config_key, config_value in config_overrides.items():
        if config_value is not None:
            setattr(config, config_key, config_value)
    
    # Handle port_forward separately since it's a boolean flag
    # Only override if the flag was explicitly provided (True)
    if args.port_forward:
        config.port_forward = True
    
    # ⚠️ Must be called before any other logging calls
    setup_logging(config.log_level, config.log_file)

    try:
        if args.command == "peer_info":
            # Get authentication token
            token = get_authentication_token(username=username, password=password, ip=args.ip, port=args.port)
            
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
            token = get_authentication_token(username=username, password=password, ip=args.ip, port=args.port)
            
            # Output the authentication token to stdout
            print(token)
        
        elif args.command == "get_integration_token":
            # Get authentication token
            token = get_authentication_token(username=username, password=password, ip=args.ip, port=args.port)

            # Create Node object with IP
            node = Node(port=args.port, token=token, ip=args.ip)
            
            # Get integration token
            integration_token = get_integration_token(node=node)
            
            # Output the integration token to stdout
            print(integration_token)
        
        elif args.command == "fail_over":
            # Get authentication token using port_peer
            token = get_authentication_token(username=username, password=password, ip=args.ip_peer, port=args.port_peer)
            
            # Create Node object with peer IP and port
            node = Node(port=args.port_peer, token=token, ip=args.ip_peer)
            
            # Call fail-over
            fail_over(node=node)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "switch_primary_secondary":
            # Get authentication token
            token = get_token(username=username, password=password, port=args.port_peer)
            
            # Create Node object
            node = Node(port=args.port_peer, token=token, ip=args.ip_peer)
            
            # Call switch-primary-secondary
            switch_primary_secondary(node=node, id=args.id)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "become_hsa":
            # Get authentication token
            token = get_token(username=username, password=password, port=args.port)
            
            # Create Node object
            node = Node(port=args.port, token=token, ip=args.ip)
            
            # Call become-hsa
            become_hsa(node=node, ip_peer=args.ip_peer, integration_token=args.integration_token)
            
            print("✓ Operation completed successfully!")

        elif args.command == "join_cluster":
            # Get authentication token for cluster node
            peer_token = get_token(username=username, password=password, port=args.port_peer)

            # Create cluster Node object
            cluster_node = Node(port=args.port_cluster, token=peer_token, ip=args.ip_cluster)

            # Get authentication token for spare node
            spare_token = get_token(username=username, password=password, port=args.port_spare)

            # Create spare Node object
            spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)

            join_cluster(cluster=spare_node, ip_spare=peer_node.ip, integration_token=args.integration_token, name=args.name)

            print("✓ Operation completed successfully!")

        elif args.command == "add_new_peer":
            # Get authentication token for cluster node
            cluster_token = get_token(username=username, password=password, port=args.port_cluster)

            # Create cluster Node object
            cluster_node = Node(port=args.port_cluster, token=cluster_token, ip=args.ip_cluster)

            # Get authentication token for spare node
            spare_token = get_token(username=username, password=password, port=args.port_spare)

            # Create spare Node object
            spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)

            # Add spare node as new peer to the cluster (with validation)
            precondition1(state=5, peer=cluster_node)
            precondition1(state=5, peer=spare_node)
            add_new_peer(
                cluster=cluster_node,
                spare=spare_node,
                name=args.name,
            )
            postcondition1(state=1, peer=spare_node)

            print("✓ Operation completed successfully!")

        elif args.command == "add_peer":
            # Get authentication token for cluster node
            cluster_token = get_token(username=username, password=password, port=args.port_cluster)

            # Create cluster Node object
            cluster_node = Node(port=args.port_cluster, token=cluster_token, ip=args.ip_cluster)
            # Get authentication token for spare node
            spare_token = get_token(username=username, password=password, port=args.port_spare)

            # Create spare Node object
            spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)

            # Add spare node as peer to the cluster
            precondition1(state=1, peer=cluster_node)
            precondition1(state=5, peer=spare_node)
            add_peer(
                cluster=cluster_node,
                spare=spare_node,
                name=args.name,
            )
            postcondition1(state=1, peer=spare_node)

            print("✓ Operation completed successfully!")

        elif args.command == "leave_cluster":
            # Get authentication token for cluster node
            cluster_token = get_token(username=username, password=password, port=args.port_cluster)

            # Create cluster Node object
            cluster_node = Node(port=args.port_cluster, token=cluster_token, ip=args.ip_cluster)

            # Get authentication token for peer node
            peer_token = get_token(username=username, password=password, port=args.port_peer)

            # Create peer Node object
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
    
            # Call leave_cluster
            leave_cluster(
                cluster=cluster_node,
                peer=peer_node,
                integration_token=args.integration_token,
            )

            print("✓ Operation completed successfully!")

        elif args.command == "remove_peer":
            # Get authentication token for cluster node
            cluster_token = get_token(username=username, password=password, port=args.port_cluster)

            # Create cluster Node object
            cluster_node = Node(port=args.port_cluster, token=cluster_token, ip=args.ip_cluster)

            # Get authentication token for peer node
            peer_token = get_token(username=username, password=password, port=args.port_peer)

            # Create peer Node object
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)

            # Call remove_peer (which will get integration token internally)
            precondition1(state=1, peer=peer_node)
            precondition1(state=1, peer=cluster_node)
            remove_peer(
                cluster=cluster_node,
                peer=peer_node,
            )
            postcondition1(state=5, peer=peer_node)

            print("✓ Operation completed successfully!")

        elif args.command == "leave_cluster_hsa":
            # Get authentication token
            token = get_token(username=username, password=password, port=args.port)
            
            # Create Node object
            node = Node(port=args.port, token=token, ip=args.ip)
            
            # Call leave-cluster-hsa
            leave_cluster_hsa(node=node, integration_token=args.integration_token)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "add_hsa":
            # Get authentication token for peer node
            peer_token = get_token(username=username, password=password, port=args.port_peer)
            
            # Get authentication token for spare node
            spare_token = get_token(username=username, password=password, port=args.port_spare)
            
            # Create Node objects
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)
            
            precondition2(state=1, peer=peer_node, hsa=spare_node)
            add_hsa(peer=peer_node, spare=spare_node)
            postcondition2(state=2, peer=peer_node, hsa=spare_node)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "add_new_hsa":
            # Get authentication token for peer node
            peer_token = get_token(username=username, password=password, port=args.port_peer)
            
            # Get authentication token for spare node
            spare_token = get_token(username=username, password=password, port=args.port_spare)
            
            # Create Node objects
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            spare_node = Node(port=args.port_spare, token=spare_token, ip=args.ip_spare)
            
            add_new_hsa(peer=peer_node, spare=spare_node)
            postcondition2(state=2, peer=peer_node, hsa=spare_node)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "remove_hsa":
            # Get authentication token for peer node
            peer_token = get_token(username=username, password=password, port=args.port_peer)
            
            # Get authentication token for HSA node
            hsa_token = get_token(username=username, password=password, port=args.port_hsa)
            
            # Create Node objects
            peer_node = Node(port=args.port_peer, token=peer_token, ip=args.ip_peer)
            hsa_node = Node(port=args.port_hsa, token=hsa_token, ip=args.ip_hsa)
            
            # Call remove_hsa
            postcondition2(state=2, peer=peer_node, hsa=hsa_node)
            remove_hsa(peer=peer_node, hsa=hsa_node)
            postcondition2(state=1, peer=peer_node, hsa=hsa_node)
            
            print("✓ Operation completed successfully!")
        
        elif args.command == "state2":
            # Get authentication tokens for each node
            token_peer = get_token(username=username, password=password, port=args.port_peer)
            token_hsa = get_token(username=username, password=password, port=args.port_hsa)
            
            # Construct Node objects
            peer_node = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa_node = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            
            # Determine the current state first
            current_state = get_state2(peer=peer_node, hsa=hsa_node)

            # Print the state table with state information
            print(state2_table(peer=peer_node, hsa=hsa_node, state=current_state))
            print()
            
            # Print state to console (stdout)
            print(f"State: {current_state}")


        elif args.command == "state1":
            token = get_token(username=username, password=password, port=args.port)
            node = Node(port=args.port, token=token, ip=args.ip)
            # Determine the current state first
            current_state = get_state1(peer=node)
            
            # Print the state table with state information
            print(state1_table(peer=node, state=current_state))
            print()
            
            # Print state to console (stdout)
            print(f"State: {current_state}")

        elif args.command == "state3":
            # Get authentication tokens for each node
            token_peer = get_token(username=username, password=password, port=args.port_peer)
            token_hsa = get_token(username=username, password=password, port=args.port_hsa)
            token_spare = get_token(username=username, password=password, port=args.port_spare)
            
            # Construct Node objects
            peer_node = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa_node = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare_node = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)
            
            # Determine the current state first
            current_state = get_state3(peer=peer_node, hsa=hsa_node, spare=spare_node)
            
            # Print the state table with state information
            print(state3_table(peer=peer_node, hsa=hsa_node, spare=spare_node, state=current_state))
            print()
            
            # Print state to console (stdout)
            print(f"State: {current_state}")
        
        elif args.command == "repaveswitch":
            # Get authentication tokens for each node
            token_peer = get_token(username=username, password=password, port=args.port_peer)
            token_hsa = get_token(username=username, password=password, port=args.port_hsa)
            token_spare = get_token(username=username, password=password, port=args.port_spare)
            
            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)
            
            # Call paverepave
            repaveswitch(peer=peer, hsa=hsa, spare=spare)
            
            print("✓ SUCCESS: Pave/Swich completed successfully!")

        elif args.command == "repave":
            # Get authentication tokens for each node
            token_peer = get_token(username=username, password=password, port=args.port_peer)
            token_hsa = get_token(username=username, password=password, port=args.port_hsa)
            token_spare = get_token(username=username, password=password, port=args.port_spare)
            
            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            spare = Node(port=args.port_spare, token=token_spare, ip=args.ip_spare)
            
            # Call repave
            repave(peer=peer, hsa=hsa, spare=spare)
            
            print("✓ SUCCESS: Repave completed successfully!")

        elif args.command == "switch":
            # Get authentication tokens for each node
            token_peer = get_token(username=username, password=password, port=args.port_peer)
            token_hsa = get_token(username=username, password=password, port=args.port_hsa)
            
            # Construct Node objects
            peer = Node(port=args.port_peer, token=token_peer, ip=args.ip_peer)
            hsa = Node(port=args.port_hsa, token=token_hsa, ip=args.ip_hsa)
            
            # Call repave
            switch(peer=peer, hsa=hsa)
            
            print("✓ SUCCESS: Switch completed successfully!")


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
