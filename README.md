# Cluster Client

Cluster Client is a command-line tool for managing NMS (Network Management System) cluster operations through the Cluster Manager and Cluster Orchestrator APIs. It provides commands for querying cluster state, managing peer and HSA (High-availability Secondary Appliance) nodes, and performing critical maintenance operations. The `repave` command orchestrates the replacement of a peer node in a cluster with a spare node by coordinating failover operations, data replication from the HSA to the spare, and role switching to make the spare the new active primary while retiring the old peer—enabling zero-downtime cluster node replacement.

## Installation

Unpack the distribution.

```bash
tar -xzf cluster-client-0.1.0.tar.gz
```

Follow instructions in INSTALL.md to install the python package.

## Using the Cluster Client

### Port forwarding

The cluster client accesses the cluster nodes either directly or via port forwarding.  For example, this peer_info API call will be forwarded via localhost:8443. 

```bash
cluster_client peer_info \
  --ip_peer 192.168.122.45\
  --port_pee 8443 \
  --port-forward 
```

When port forwarding is active, the API requests will be directed to `https://localhost:8443/api/v3/`.  When port forwarding is inactive, API requests will be directed to `https://192.168.122.45:8443/api/v3/`.  Port forwarding is inactive by default.  The default configuration can be overriden by an using an environment variable

```bash
export CLUSTER_CLIENT_PORT_FORWARD=1 # Use port forwarding by default
```

### Authentication

Authentication tokens are retrieved using the signin API.  A valid userid and password must be specified to the command either by using `--username` and `--password` or by setting a environment variables.

```bash
export CLUSTER_CLIENT_USERNAME="admin"
export CLUSTER_CLIENT_PASSWORD="secret"
```

**Important:** When a spare NMS node is configured, the default password must be changed using the GUI before the API functions can be used. The API will not accept authentication with the default password on spare nodes.

## Logging

The Cluster Client provides flexible logging capabilities to help monitor operations and troubleshoot issues.

### Logging Configuration

Logging can be configured using command-line options:

```bash
cluster_client <command> --log-level INFO --log-file cluster_client.log
```

Or by setting environment variables:

```bash
export CLUSTER_CLIENT_LOG_LEVEL=DEBUG
export CLUSTER_CLIENT_LOG_FILE=/var/log/cluster_client.log
```

### Log Levels

The `--log-level` option controls the verbosity of console output. Available levels are:

- **DEBUG**: Detailed diagnostic information for troubleshooting
- **INFO**: General informational messages about operation progress (default)
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for severe failures

### File Logging

When the `--log-file` option is specified, logs are written to the specified file **at INFO level**, regardless of the console log level setting. This ensures that important operational information is always captured to the file for audit and troubleshooting purposes.

**Key behaviors:**

- Console output respects the configured `--log-level`
- File output is always at INFO level when `--log-file` is specified
- Both console and file logs use the same timestamp format: `YYYY-MM-DD HH:MM:SS,mmm [LEVEL] module: message`

### Example Usage

View detailed debug information on console only:
```bash
cluster_client peer_info --ip_peer 192.168.122.45 --port_peer 8443 --log-level DEBUG
```

Log INFO and above to file while showing only warnings on console:
```bash
cluster_client repave \
  --ip_peer 192.168.122.45 --port_peer 8443 \
  --ip_hsa 192.168.122.22 --port_hsa 8444 \
  --ip_spare 192.168.122.217 --port_spare 8445 \
  --log-level WARNING \
  --log-file /var/log/cluster_repave.log
```

In this example, the console will only show WARNING, ERROR, and CRITICAL messages, while the log file will capture all INFO level and above messages for a complete operational record.

## Client commands

The Cluster Client provides additional commands to configure the NMS cluster via the API.

### Basic API calls

The basic commands request authentication tokens and then issue single API calls.

**Note:** You can see the available options for each command by using the `--help` flag. For example:
```bash
cluster_client peer_info --help
```

| Command                  | API call<br>api/v3/                      | Description                                            |
| ------------------------ | ---------------------------------------- | ------------------------------------------------------ |
| peer_table               | peers                                    | Display peer information                               |
| get_integration_token    | cluster-orchestrator/integration-token   | Retrieve integration token                             |
| become_hsa               | cluster-orchestrator/become-hsa          | Make a spare node become an HSA                        |
| leave_cluster_hsa        | cluster-orchestrator/leave-cluster       | HSA node leave the cluster                             |
| join_cluster             | cluster-orchestrator/join-cluster        | Add a node to an existing cluster                      |
| leave_cluster            | cluster-orchestrator/leave-cluster       | Remove a node from the cluster                         |
| fail_over                | cluster-manager/fail-over                | Perform fail-over operation                            |
| switch_primary_secondary | cluster-manager/switch-primary-secondary | Switch primary and secondary appliance roles on a peer |

### Composite API calls

These composite commands request authentication tokens, verify prerequisites and then issue multiple API calls. 

| Command      | Description                                                                |
| ------------ | -------------------------------------------------------------------------- |
| repave       | Perform the Repave Procedure given a peer, hsa and spare.                  |
| repaveswitch | Perform the Repave and Switch Procedures given a peer, hsa and spare.      |

### Repave Procedure

The Repave Procedure replaces a peer in a NMS cluster with a spare.  

In this example, the `state` command shows the Peer, its HSA and a Spare node.  The Peer is the active primary.  The HSA is the passive secondary.

| Field              | Peer                 | HSA                  | Spare                |
|--------------------|----------------------|----------------------|----------------------|
| ip                 | 192.168.122.45       | 192.168.122.22       | 192.168.122.217      |
| port               | 8443                 | 8444                 | 8445                 |
| active_appliance   | Primary              | Primary              | N/A                  |
| primary_ip         | 192.168.122.45       | 192.168.122.45       | N/A                  |
| secondary_ip       | 192.168.122.22       | 192.168.122.22       | N/A                  |
| id                 | 1                    | 1                    | N/A                  |
| status             | active primary       | passive secondary    | spare                |

The Spare is an nms node that has been "Paved".  Paving is the process of installing a virtual machine, installing the NMS image and upgraded the NMS software to the same version as the peers in the cluster.

The purpose of the `repave` command is to Repave the Spare.  Repaving is the process of replicating the Peer's data to the Spare.  The `repave` command will cause the HSA to become the active primary.  The Spare will become the passive secondary and replication will start.  The peer will be retired.

```bash
cluster_client repave \
  --ip_peer 192.168.122.45\
  --port_pee 8443 \
  --ip_hsa 192.168.122.22 \
  --port_hsa 8444 \
  --ip_spare 192.168.122.217 \
  --port_spare 8445
```

| Field              | Peer                 | HSA                  | Spare                |
|--------------------|----------------------|----------------------|----------------------|
| ip                 | 192.168.122.45       | 192.168.122.22       | 192.168.122.217      |
| port               | 8443                 | 8444                 | 8445                 |
| active_appliance   | N/A                  | Primary              | N/A                  |
| primary_ip         | N/A                  | 192.168.122.22       | N/A                  |
| secondary_ip       | N/A                  |                      | N/A                  |
| id                 | N/A                  | 1                    | N/A                  |
| status             | retired              | active primary       | spare                |

The replication of data from the HSA to the Spare may take a long time.  When it is complete the status shall be:

| Field              | Peer                 | HSA                  | Spare                |
|--------------------|----------------------|----------------------|----------------------|
| ip                 | 192.168.122.45       | 192.168.122.22       | 192.168.122.217      |
| port               | 8443                 | 8444                 | 8445                 |
| active_appliance   | N/A                  | Primary              | Primary              |
| primary_ip         | N/A                  | 192.168.122.22       | 192.168.122.22       |
| secondary_ip       | N/A                  | 192.168.122.217      | 192.168.122.217      |
| id                 | N/A                  | 1                    | 1                    |
| status             | retired              | active primary       | passive secondary    |

The data has been coped to the Spare, but the Spare is still a passive secondary.  When replication is complete the `repaveswitch` command can be used to make the Spare into the new active primary.  When the process is complete, the HSA will once again be the passive secondary.

```bash
cluster_client repaveswitch \
  --ip_peer 192.168.122.45\
  --port_pee 8443 \
  --ip_hsa 192.168.122.22 \
  --port_hsa 8444 \
  --ip_spare 192.168.122.217 \
  --port_spare 8445
```

| Field              | Peer                 | HSA                  | Spare                |
|--------------------|----------------------|----------------------|----------------------|
| ip                 | 192.168.122.45       | 192.168.122.22       | 192.168.122.217      |
| port               | 8443                 | 8444                 | 8445                 |
| active_appliance   | N/A                  | Primary              | Primary              |
| primary_ip         | N/A                  | 192.168.122.217      | 192.168.122.217      |
| secondary_ip       | N/A                  | 192.168.122.22       | 192.168.122.22       |
| id                 | N/A                  | 1                    | 1                    |
| status             | retired              | passive secondary    | active primary.      |


It is important to note that the parameters of the `repave` and `repaveswitch` commands reflect the state of the Peer, HSA and Spare **at the time the `repave` command starts**.  The commands are re-startable.  They must be restarted using these initial parameter values.  In this example, the `repaveswitch` `--ip_spare` parameter value shall be `192.168.122.217`, as it was in the `repave` command, even though that node is not a spare at the time the `repaveswitch` command is issued.

### Configuration options

Configuration defaults can be overridden by command line parameters or by environment variables prefixed by `CLUSTER_CLIENT_`.  For example, the optional `--http_timeout_value` parameter overrides the CLUSTER_CLIENT_HTTP_TIMEOUT_VALUE environment variable which overrides the default.  Run `cluster_client show_config` to show the default configuration values.

| Option                                                                        | Description                                                           |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`                             | Set the logging level.                                                |
| `--log-file LOG_FILE`                                                         | Log to file instead of console.                                       |
| `--username USERNAME`                                                         | Username for authentication.                                          |
| `--password PASSWORD`                                                         | Password for authentication.                                          |
| `--host HOST`                                                                 | Host used for port forwarding                                         |
| `--http_502_max_retries HTTP_502_MAX_RETRIES`                                 | Maximum number of retries when a HTTP 502 response is received.       |
| `--http_502_retry_delay HTTP_502_RETRY_DELAY`                                 | Delay between retries when a HTTP 502 response is received.           |
| `--http_timeout_value HTTP_TIMEOUT_VALUE`                                     | The timeout value for HTTP requests.                                  |
| `--wait_state_max_retries WAIT_STATE_MAX_RETRIES`                             | Maximum number of retries when waiting for a state to be reached.     |
| `--wait_state_initial_delay WAIT_STATE_INITIAL_DELAY`                         | Initial delay before waiting for a state to be reached.               |
| `--wait_state_retry_delay WAIT_STATE_RETRY_DELAY`                             | Delay between retries when waiting for a state to be reached.         |
| `--wait_state_settle_delay WAIT_STATE_SETTLE_DELAY`                           | Final delay after waiting for a state to be reached.                  |
| `--switch_primary_secondary_max_retries SWITCH_PRIMARY_SECONDARY_MAX_RETRIES` | Maximum number of retries when switching primary and secondary nodes. |
| `--switch_primary_secondary_retry_delay SWITCH_PRIMARY_SECONDARY_RETRY_DELAY` | Delay between retries when switching primary and secondary nodes.     |
| `--fail_over_max_retries FAIL_OVER_MAX_RETRIES`                               | Maximum number of retries when failing over to the secondary.         |
| `--fail_over_retry_delay FAIL_OVER_RETRY_DELAY`                               | Delay between retries when failing over to the secondary.             |
| `--port_forward`                                                              | Enable port forwarding.                                               |


