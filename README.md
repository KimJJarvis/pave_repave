# Pave Repave Procedure

## Pave Procedure

The Pave Procedure replaces a peer in a NMS cluster.

The peer node will be replaced by its secondary and retired.  Initially, the peer must be an active node in the NMS cluster and it must have a passive secondary.  When the Procedure is complete, the secondary node will be the active peer in the NMS cluster and the peer will be retired.

| Action v3/api                            | Target | State | Active    | Primary | Secondary | Retired |
| ---------------------------------------- | ------ | ----- | --------- | ------- | --------- | ------- |
| Initial state                            |        | 1     | Primary   | A       | B         |         |
| cluster-manager/fail-over                | A      | 2     | Secondary | A       | B         |         |
| cluster-manager/switch-primary-secondary | B      | 3     | Primary   | B       | A         |         |
| cluster-orchestrator/integration-token   | B      |       | Primary   | B       | A         |         |
| cluster-orchestrator/leave_cluster_hsa   | A      | 4     | Primary   | B       |           | A       |

- **A,B** NMS Nodes.
- **Action v3/api** The API call.
- **Target** The target node to which the API call is sent.
- **State** The state of the cluster prior to the action. States are listed in the table below.
- **Active** The active node in the peers table.
- **Primary** The primary node in the peers table.
- **Secondary** The secondary node in the peers table.
- **Retired** The retired node which will not appare in the peers table.

## Repave Procedure

The Repave Procedure ensures high availability for a peer in a NMS cluster.

The peer node will be replaced by a spare node. Initially, the peer must not have a secondary.  When the procedure is complete, the spare node will be the active peer in the NMS cluster, the peer will be its secondary.


| Action v3/api                            | Target | State | Active    | Primary | Secondary | Spare |
| ---------------------------------------- | ------ | ----- | --------- | ------- | --------- | ----- |
| Initial state                            |        | 5     | Pimary    | B       |           | C     |
| cluster-orchestrator/integration-token   | B      |       | Primary   | B       |           | C     |
| cluster-orchestrator/become_hsa          | C      | 1     | Primary   | B       | C         |       |
| cluster-manager/fail-over                | B      | 2     | Secondary | B       | C         |       |
| cluster-manager/switch-primary-secondary | C      | 3     | Primary   | C       | B         |       |

- **B,C** NMS Nodes.
- **Action v3/api** The API call.
- **Target** The target node to which the API call is sent.
- **State** The state of the cluster prior to the action. States are listed in the table below.
- **Active** The active node in the peers table.
- **Primary** The primary node in the peers table.
- **Secondary** The secondary node in the peers table.
- **Spare** A spare node which will join the cluster.

## State 

| State | Peer<br>active_applicance | Peer<br>primary_ip | Peer<br>secondary_ip | Other             | Other<br>found | Other<br>active_appliance | Other<br>primary_ip | Other<br>secondary_ip |
| ----- | ------------------------- | ------------------ | -------------------- | ----------------- | -------------- | ------------------------- | ------------------- | --------------------- |
| 1     | Primary                   | peer.ip            | other.ip             | Passive secondary | true           | 1                         | peer.ip             | other.ip              |
| 2     | Secondary                 | peer.ip            | other.ip             | Active secondary  | true           | 2                         | peer.ip             | other.ip              |
| 3     | Primary                   | other.ip           | peer.ip              | Primary           | true           | 1                         | hsa.ip              | peer.ip               |
| 4     | Primary                   | peer.ip            | ""                   | Retired           | true           | ?                         | ?                   | ?                     |
| 5     | Primary                   | peer.ip            | ""                   | Spare             | false          | ?                         | ?                   | ?                     |


During the Pave Repave processes it is necessary to wait for the NMS system to achieve a target state before proceeding with the next API call.
One node is a peer in the cluster, the other could be its passive secondary (state 1), its active secondary (state 2), its primary (state 3), retired (state 4) or spare (state 5).   
State is determined by calling the gRPC endpoint GET api.v3.peers on both nodes.  

## Manual Procedure Pave

The peer, node A. will be replaced by its secondary, node B, and retired. 

Set environment variables:
- $TOKEN_CLUSTER Bearer token for authentication
- $IP_A IP address of the peer node A (in dot format)
- $PORT_A Port number for peer node A

#### Get peer information

Get the IP and port number of node B and the peer ID.

```bash
uv run peer_info --token_peer $TOKEN_CLUSTER --ip $IP_A --port $PORT_A
```

Set environment variables:

- $IP_B IP address of the HSA node B (in dot format)
- $PORT_B Port number for HSA node B
- $ID id of the peer/HSA pair A,B
- 
#### Confirm state

Confirm initial state for pave operation.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_A --port_peer $PORT_A --token_other $TOKEN_CLUSTER --ip_other $IP_B --port_other $PORT_B
```

Confirm that the returned state is 1.

#### Fail over

Initiate fail over on node A.

```bash
uv run fail_over --token_peer $TOKEN_CLUSTER --ip_peer $IP_A --port_peer $PORT_A
```

Wait for 30 seconds before continuing.

#### Confirm state

Fail over is an asynchronous process.  Wait for state 2.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --token_other $TOKEN_CLUSTER --ip_other $IP_A --port_other $PORT_A
```

Confirm that the returned state is 2.

#### Switch Primary Secondary

Perform the switch on node B, which is the new primary.

```bash
uv run switch_primary_secondary --token $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B
```

Wait for 30 seconds before continuing.

#### Confirm state

Swith primary secondary is a synchronous process.  Wait for state 3.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --token_other $TOKEN_CLUSTER --ip_other $IP_A --port_other $PORT_A
```

Confirm that the returned state is 3.

#### Get an integration token

Get an integration token from node B.

```bash
uv run get_integration_token --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B
```

Set environment variable:
- $INTEGRATION_TOKEN

#### Leave cluster HSA

Initiate leave cluster HSA on node A.

```bash
uv run leave_cluster_hsa --token_hsa $TOKEN_CLUSTER --ip_hsa $IP_A --port_hsa $PORT_A
```

Wait for 30 seconds before continuing.

#### Confirm state

Leave cluster HSA is an asynchronous process.  Wait for state 4.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --token_other $TOKEN_CLUSTER --ip_other $IP_A --port_other $PORT_A
```

Confirm that the returned state is 4.

The node B is now a peer in the cluster.  The node A has been retired.

## Manual Procedure Repave

The peer, node B, will be replaced by a spare, node C.

Set environment variables:
- $TOKEN_CLUSTER Bearer token for authentication
- $IP_B IP address of the peer node B (in dot format)
- $PORT_B Port number for peer node B
- $IP_C IP address of the spare node C (in dot format)
- $PORT_C Port number of the spare node C

#### Get peer information

Get the peer ID.

```bash
uv run peer_info --token_peer $TOKEN_CLUSTER --ip $IP_B --port $PORT_B
```

Set environment variable:
- $ID id of the peer B

#### Confirm state

Confirm initial state for pave operation.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --token_other $TOKEN_CLUSTER --ip_other $IP_C --port_other $PORT_C
```

Confirm that the returned state is 5.

#### Get an integration token

Get an integration token from node B.

```bash
uv run get_integration_token --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B
```

Set environment variable:
- $INTEGRATION_TOKEN

#### Become HSA

Initiate become HSA on node C.

```bash
uv run leave_cluster_hsa --token_hsa $TOKEN_CLUSTER --ip_hsa $IP_C --port_hsa $PORT_C
```

Wait for 30 seconds before continuing.

#### Confirm state

Become HSA is an asynchronous process.  Wait for state 1.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --token_other $TOKEN_CLUSTER --ip_other $IP_C --port_other $PORT_C
```

Confirm that the returned state is 1.

#### Fail over

Initiate fail over on node B.

```bash
uv run fail_over --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B
```

Wait for 30 seconds before continuing.

#### Confirm state

Fail over is an asynchronous process.  Wait for state 2.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --token_other $TOKEN_CLUSTER --ip_other $IP_C --port_other $PORT_C
```

Confirm that the returned state is 2.

#### Switch Primary Secondary

Perform the switch on node C, which is the new primary.

```bash
uv run switch_primary_secondary --token $TOKEN_CLUSTER --ip_peer $IP_C --port_peer $PORT_C
```

Wait for 30 seconds before continuing.

#### Confirm state

Switch primary secondary is a synchronous process.  Wait for state 3.

```bash
uv run get_state --token_peer $TOKEN_CLUSTER --ip_peer $IP_C --port_peer $PORT_C --token_other $TOKEN_CLUSTER --ip_other $IP_B --port_other $PORT_B
```

Confirm that the returned state is 3.

Node C is now the active primary and node B is its passive secondary (HSA). 

## Automated Procedure Pave

The peer, node A. will be replaced by its secondary, node B, and retired. 

Set environment variables:
- $TOKEN_CLUSTER Bearer token for authentication
- $IP_A IP address of the peer node A (in dot format)
- $PORT_A Port number for peer node A

#### Get peer information

Get the IP and port number of node B and the peer ID.

```bash
uv run peer_info --token_peer $TOKEN_CLUSTER --ip $IP_A --port $PORT_A
```

Set environment variable:
- $IP_B IP address of the HSA node B (in dot format)
- $PORT_B Port number for HSA node B

#### Pave

```bash
uv run pave --token_peer $TOKEN_CLUSTER --ip_peer $IP_A --port_peer $PORT_A --ip_hsa $IP_B --port_hsa $PORT_B
```

The node B is now a peer in the cluster.  The node A has been retired.

## Automated Procedure Repave

The peer, node B, will be replaced by a spare, node C.

Set environment variables:
- $TOKEN_CLUSTER Bearer token for authentication
- $IP_B IP address of the peer node B (in dot format)
- $PORT_B Port number for peer node B
- $IP_C IP address of the spare node C (in dot format)
- $PORT_C Port number of the spare node C

#### Repave

```bash
uv run pave --token_peer $TOKEN_CLUSTER --ip_peer $IP_B --port_peer $PORT_B --ip_hsa $IP_C --port_hsa $PORT_C
```

Node C is now the active primary and node B is its passive secondary (HSA). 

## Client applications

### peer_info

```bash
Calls the gRPC endpoint api.v3.peers on the node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token TOKEN         Bearer token for authentication
  --ip IP               IP address of the node (in dot format)
  --port PORT           Port number of the node
```

### become_hsa

```bash
Calls the gRPC endpoint api.v3.cluster-orchestrator.become-hsa on a spare node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token_spare TOKEN_SPARE
                        Bearer token for authentication on spare node
  --ip_spare IP_SPARE   IP address of the spare node (dot format)
  --port_spare PORT_SPARE
                        Port number of the spare node
  --ip_peer IP_PEER     Primary/Peer IP address in the cluster (dot format)
  --integration_token INTEGRATION_TOKEN
                        Integration token
```

### fail_over

```bash
Calls the gRPC endpoint api.v3.cluster-manager.fail-over on a peer node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token_peer TOKEN_PEER
                        Bearer token for authentication on peer
  --ip_peer IP_PEER     IP address of the peer node to fail-over
  --port_peer PORT_PEER
                        Port number of the peer node
```

### get_integration_token

```bash
Calls the gRPC endpoint api.v3.cluster-orchestrator.integration-token on a node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token TOKEN         Bearer token for authentication
  --ip_peer IP_PEER     IP address of peer (dot format)
  --port_peer PORT_PEER
                        Port number for peer
```

### get_state 

```bash
Calls the gRPC endpoint api.v3.peers on the peer node and another node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token_peer TOKEN_PEER
                        Bearer token for peer authentication
  --ip_peer IP_PEER     IP address of the peer node
  --port_peer PORT_PEER
                        Port number for peer node
  --token_other TOKEN_OTHER
                        Bearer token for Other authentication
  --ip_other IP_OTHER   IP address of the Other node
  --port_other PORT_OTHER
                        Port number for Other node
```

### leave_cluster_hsa

```bash
Calls the gRPC endpoint api.v3.cluster-orchestrator.leave-cluster-hsa on a HSA node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token_hsa TOKEN_HSA
                        Bearer token for authentication on HSA
  --ip_hsa IP_HSA       IP address of the HSA (dot format)
  --port_hsa PORT_HSA   Port number of the HSA
  --integration_token INTEGRATION_TOKEN
                        Integration token
```

### switch_primary_secondary

```bash
Calls the gRPC endpoint api.v3.cluster-manager.switch-primary-secondary on a peer node.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token TOKEN         Bearer token for authentication
  --ip_peer IP_PEER     IP address of the peer (dot format)
  --port_peer PORT_PEER
                        Port number of the peer
  --id ID               ID of the peer in the peers table
```

### pave

```bash
The Pave Procedure replaces a peer in a NMS cluster

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --ip_peer IP_PEER     IP address of the peer node (dot format)
  --token_peer TOKEN_PEER
                        Bearer token for peer authentication
  --port_peer PORT_PEER
                        Port number for peer node
  --ip_hsa IP_HSA       IP address of the HSA node (dot format)
  --port_hsa PORT_HSA   Port number for HSA node
```

### repave

```bash
The Repave Procedure ensures high availability for a peer in a NMS cluster.

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --log-file LOG_FILE   Log to file instead of console
  --token_peer TOKEN_PEER
                        Bearer token for peer authentication
  --ip_peer IP_PEER     IP address of the peer node (dot format)
  --port_peer PORT_PEER
                        Port number for peer node
  --token_spare TOKEN_SPARE
                        Bearer token for spare authentication
  --ip_spare IP_SPARE   IP address of the spare node (dot format)
  --port_spare PORT_SPARE
                        Port number for spare node
```
