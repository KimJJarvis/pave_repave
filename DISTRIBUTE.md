# Distribution Instructions for Cluster Client

This document provides instructions for creating a tar file distribution package of the Cluster Client software.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Creating the Distribution Package](#creating-the-distribution-package)
- [Distribution Checklist](#distribution-checklist)
- [Quick Reference](#quick-reference)

## Prerequisites

- Python 3.12 or higher
- `tar` utility (standard on Unix/Linux/macOS)
- Access to the source repository
- Write permissions in the parent directory

## Creating the Distribution Package

### Step 1: Navigate to Parent Directory

Navigate to the parent directory of the project:
```bash
cd /path/to/parent_directory
```

The project directory should be named `pave_repave`.

### Step 2: Create the Tar Archive

Create a tar.gz archive of the project, excluding unnecessary files:

```bash
tar -czf cluster-client-0.1.0.tar.gz \
    --exclude='pave_repave/.git' \
    --exclude='pave_repave/.venv' \
    --exclude='pave_repave/venv' \
    --exclude='pave_repave/__pycache__' \
    --exclude='pave_repave/*.pyc' \
    --exclude='pave_repave/.env' \
    --exclude='pave_repave/.env.*' \
    --exclude='pave_repave/dist' \
    --exclude='pave_repave/build' \
    --exclude='pave_repave/*.egg-info' \
    pave_repave/
```

This command will:
- Create a compressed tar archive named `cluster-client-0.1.0.tar.gz`
- Exclude version control files (`.git`)
- Exclude virtual environments (`.venv`, `venv`)
- Exclude Python cache files (`__pycache__`, `*.pyc`)
- Exclude environment configuration files (`.env*`)
- Exclude build artifacts (`dist`, `build`, `*.egg-info`)

### Step 3: Verify the Archive

Check the contents of the archive:
```bash
tar -tzf cluster-client-0.1.0.tar.gz | head -20
```

Expected contents should include:
- `pave_repave/pyproject.toml`
- `pave_repave/README.md`
- `pave_repave/LICENSE`
- `pave_repave/INSTALL.md`
- `pave_repave/src/cluster_client/` directory with Python files
- `pave_repave/tests/` directory

### Step 4: Verify Archive Size

Check that the archive size is reasonable:
```bash
ls -lh cluster-client-0.1.0.tar.gz
```

Expected size: < 1 MB for source distribution

### Step 5: Test Extraction

Test that the archive extracts correctly:
```bash
# Create a temporary directory for testing
mkdir -p /tmp/test_extract
cd /tmp/test_extract

# Extract the archive
tar -xzf /path/to/cluster-client-0.1.0.tar.gz

# Verify the structure
ls -la pave_repave/

# Clean up
cd ..
rm -rf /tmp/test_extract
```

## Distribution Checklist

Before distributing the tar file, verify:

- [ ] All source files are included
- [ ] `pyproject.toml` is present and correct
- [ ] `README.md` documentation is up to date
- [ ] `INSTALL.md` installation instructions are included
- [ ] `LICENSE` file is included
- [ ] Version number is correct in `pyproject.toml`
- [ ] Dependencies are specified correctly in `pyproject.toml`
- [ ] `.git` directory is excluded
- [ ] Virtual environments (`.venv`, `venv`) are excluded
- [ ] Cache files (`__pycache__`, `*.pyc`) are excluded
- [ ] Environment files (`.env`, `.env.*`) are excluded
- [ ] Build artifacts (`dist`, `build`, `*.egg-info`) are excluded
- [ ] Archive extracts to `pave_repave/` directory
- [ ] Archive size is reasonable (< 1 MB for source)
- [ ] Archive can be extracted successfully
- [ ] Extracted files have correct permissions

## Quick Reference

### Creating Package
```bash
cd /path/to/parent_directory
tar -czf cluster-client-0.1.0.tar.gz \
    --exclude='pave_repave/.git' \
    --exclude='pave_repave/.venv' \
    --exclude='pave_repave/__pycache__' \
    --exclude='pave_repave/*.pyc' \
    --exclude='pave_repave/.env*' \
    --exclude='pave_repave/dist' \
    --exclude='pave_repave/build' \
    --exclude='pave_repave/*.egg-info' \
    pave_repave/
```

### Verifying Package
```bash
# Check contents
tar -tzf cluster-client-0.1.0.tar.gz | head -20

# Check size
ls -lh cluster-client-0.1.0.tar.gz

# Test extraction
tar -xzf cluster-client-0.1.0.tar.gz
```

## Version Management

When creating a new release:

1. Update the version number in `pyproject.toml`
2. Update the version number in the tar filename (e.g., `cluster-client-0.2.0.tar.gz`)
3. Update the "Last Updated" date in documentation files
4. Create a changelog or release notes if applicable

## Distribution Methods

The tar file can be distributed via:

- **File Transfer**: Direct file transfer (scp, sftp, rsync)
- **Web Server**: Host on a web server for download
- **Email**: Attach to email (if size permits)
- **Shared Storage**: Place in shared network storage
- **Version Control**: Tag releases in git repository

## Security Considerations

Before distributing:

- Ensure no sensitive information (passwords, tokens, keys) is included
- Verify that `.env` and `.env.*` files are excluded
- Check that no personal or proprietary data is in the archive
- Consider creating a checksum file for integrity verification:
  ```bash
  sha256sum cluster-client-0.1.0.tar.gz > cluster-client-0.1.0.tar.gz.sha256
  ```

## Additional Resources

- **INSTALL.md**: Installation instructions for end users
- **README.md**: Comprehensive usage documentation
- **LICENSE**: Software license information

---

**Version:** 0.1.0  
**Last Updated:** 2026-06-02