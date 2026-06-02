# Installation Instructions for Cluster Client

This document provides instructions for installing the Cluster Client software from a tar file distribution.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installing from Tar File](#installing-from-tar-file)
- [Post-Installation Configuration](#post-installation-configuration)
- [Verification](#verification)
- [Uninstallation](#uninstallation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.12 or higher
- `pip` (Python package installer)
- Sufficient disk space (~10 MB)
- Network access (for installing dependencies)

## Installing from Tar File

### Step 1: Extract the Archive

```bash
tar -xzf cluster-client-0.1.0.tar.gz
cd pave_repave
```

### Step 2: Create a Virtual Environment

It is strongly recommended to install the package in a virtual environment to avoid conflicts with other Python packages:

```bash
python3 -m venv .venv
```

### Step 3: Activate the Virtual Environment

**On Linux/macOS:**
```bash
source .venv/bin/activate
```

**On Windows:**
```cmd
.venv\Scripts\activate
```

You should see `(.venv)` prefix in your command prompt indicating the virtual environment is active.

### Step 4: Install the Package

Install the package and its dependencies:

```bash
pip install .
```

This will:
- Install the cluster-client package
- Install required dependencies (pydantic >= 2.13.4, pydantic-settings >= 2.14.1)
- Make the `cluster_client` command available

## Post-Installation Configuration

### Step 1: Verify Installation

Check that the command-line tool is available:
```bash
cluster_client --help
```

You should see the help message with available commands.

### Step 2: Set Up Environment Variables (Optional)

Configure default settings using environment variables:

```bash
# Create a configuration file (optional)
cat > ~/.cluster_client_env << 'EOF'
export CLUSTER_CLIENT_USERNAME="admin"
export CLUSTER_CLIENT_PASSWORD="your_password"
export CLUSTER_CLIENT_PORT_FORWARD=0
export CLUSTER_CLIENT_LOG_LEVEL="INFO"
EOF

# Load the configuration
source ~/.cluster_client_env
```

Or add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
echo 'source ~/.cluster_client_env' >> ~/.bashrc
```

### Step 3: Test Basic Functionality

Test a simple command (requires a running cluster):
```bash
cluster_client peer_info \
    --ip_peer 192.168.122.45 \
    --port_peer 8443 \
    --username admin \
    --password secret
```

## Verification

### Verify Package Installation

```bash
# Check installed package
pip show cluster-client

# List installed files
pip show -f cluster-client

# Verify command availability
which cluster_client

# Check that the command works
cluster_client --help
```

### Verify Dependencies

```bash
# List all dependencies
pip list | grep -E "(pydantic|pydantic-settings)"
```

Expected dependencies:
- pydantic >= 2.13.4
- pydantic-settings >= 2.14.1

## Uninstallation

### Remove the Package

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Uninstall the package
pip uninstall cluster-client

# Deactivate and remove virtual environment
deactivate
cd ..
rm -rf pave_repave/
```

### Clean Up Configuration Files

```bash
# Remove environment configuration (if created)
rm -f ~/.cluster_client_env

# Remove any log files
rm -f cluster_client.log
```

## Troubleshooting

### Issue: Command not found after installation

**Cause:** Virtual environment is not activated.

**Solution:** Activate the virtual environment:
```bash
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Issue: Permission denied during installation

**Cause:** Attempting to install without proper permissions or outside a virtual environment.

**Solution:** Ensure you're using a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### Issue: Dependency conflicts

**Cause:** Conflicting packages in the environment.

**Solution:** Create a fresh virtual environment:
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

### Issue: Python version mismatch

**Cause:** Python version is older than 3.12.

**Solution:** Ensure Python 3.12 or higher is installed:
```bash
python3 --version
```

If the version is too old, install Python 3.12 or higher from [python.org](https://www.python.org/downloads/).

### Issue: pip not found

**Cause:** pip is not installed or not in PATH.

**Solution:** Install pip or use the ensurepip module:
```bash
python3 -m ensurepip --upgrade
```

## Quick Reference

### Installing Package
```bash
tar -xzf cluster-client-0.1.0.tar.gz
cd pave_repave
python3 -m venv .venv
source .venv/bin/activate
pip install .
cluster_client --help
```

### Uninstalling Package
```bash
source .venv/bin/activate
pip uninstall cluster-client
deactivate
```

## Additional Resources

- **README.md**: Comprehensive usage documentation
- **LICENSE**: Software license information
- **pyproject.toml**: Package metadata and dependencies
- **DISTRIBUTE.md**: Instructions for creating distribution packages

For detailed usage instructions and examples, refer to the README.md file included in the distribution.

---

**Version:** 0.1.0  
**Last Updated:** 2026-06-02