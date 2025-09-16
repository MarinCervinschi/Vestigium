# Vestigium Stress Tests Documentation

This document describes the performance stress tests for Vestigium VCS and how to use them effectively.

## Overview

The stress tests are designed to evaluate Vestigium's performance under various challenging conditions:

- **Large file handling**: Testing with files from 1MB to 50MB+
- **Many files operations**: Testing with hundreds to thousands of files
- **Complex scenarios**: Mixed file types, deep directory structures, binary files
- **Resource monitoring**: Tracking execution time and system resource usage

## Quick Start

```bash
# Run all stress tests in Docker
docker compose run --rm vestigium-stress
```

## Test Categories

### 1. Large File Tests (`test_large_files.py`)

Tests how Vestigium handles files of increasing sizes:

- **Small large files**: 1MB, 5MB (quick validation)
- **Medium large files**: 10MB, 25MB (realistic scenarios)
- **Large files**: 50MB+ (stress scenarios)

**Operations tested**:
- `ves add` with large files
- `ves commit` with large files
- `ves status` with large files in repository
- Batch operations with multiple large files

**Example output**:
```
Large file add (10MB):
  Execution time: 0.85s

Large file commit (10MB):
  Execution time: 1.23s
```

### 2. Many Files Tests (`test_many_files.py`)

Tests performance with numerous files:

- **Small scale**: 50-100 files (quick validation)
- **Medium scale**: 200-500 files (realistic scenarios)
- **Large scale**: 1000+ files (stress scenarios)

**Scenarios tested**:
- Many small files in flat structure
- Deep directory structures
- Binary files with various content types
- Incremental additions
- Mixed file operations

**Example output**:
```
Many files add (500 files):
  Execution time: 2.15s
  Files/second: 232.56
```

### 3. Mixed Operations Tests

Complex scenarios combining:
- Different file sizes
- Various file types (text, binary, symlinks)
- Deep directory structures
- Sequential operations (add → commit → status)

## Running Stress Tests

### Using Docker (Recommended)

```bash
# Run all stress tests
docker compose run --rm vestigium-stress
```

The `vestigium-stress` service is pre-configured in `docker-compose.yml` with the appropriate command and settings for stress testing.

### Direct Docker Commands

```bash
# Run all stress tests (same as above)
docker compose run --rm vestigium-stress
```

For custom test execution, you can override the default command:

```bash
# Run with custom parameters
docker compose run --rm vestigium-stress python -m pytest tests/stress/ -v -k "not 1000"
```

### Direct pytest Commands (Local)

```bash
# Run all stress tests (local - not recommended)
pytest tests/stress/ -v -m stress

# Run only large file tests
pytest tests/stress/test_large_files.py -v

# Run only many files tests
pytest tests/stress/test_many_files.py -v

# Run quick tests only (skip largest datasets)
pytest tests/stress/ -v -m stress -k "not (50mb or 100mb or 1000)"
```

**Note**: Local execution is not recommended. Use Docker for consistent, isolated testing environment.

## Understanding Results

### Performance Metrics

The tests report several key metrics:

- **Execution Time**: Total time for the operation
- **Throughput**: Files/second or MB/second for batch operations
- **Resource Usage**: Memory consumption during operations (when available)

### Performance Expectations

Based on typical hardware, here are rough performance expectations:

**Large Files**:
- 1-10MB files: < 2 seconds per add operation
- 25-50MB files: < 10 seconds per add operation
- Commit operations: Usually 2-3x slower than add

**Many Files**:
- 50-100 files: > 20 files/second
- 500+ files: > 10 files/second
- Deep structures: Should not significantly slow down operations

### Interpreting Failures

Common reasons for test failures:

1. **Timeout**: Operation took longer than expected
   - Check available disk I/O performance
   - Verify sufficient RAM is available
   - Try `--quick` mode for smaller datasets

2. **Resource Exhaustion**: Out of memory or disk space
   - Stress tests create temporary files up to 50MB+ each
   - Ensure at least 1GB free disk space
   - Consider reducing test parameters

3. **Environment Issues**: 
   - Slow containers or virtual environments
   - Background processes consuming resources
   - Try running tests at different times

## Customizing Tests

### Modifying Test Parameters

You can customize the test datasets by editing the test files:

```python
# In test_large_files.py
@pytest.mark.parametrize("file_size_mb", [1, 5, 10, 25])  # Customize sizes

# In test_many_files.py  
@pytest.mark.parametrize("num_files", [50, 100, 500])     # Customize counts
```

### Adding New Stress Tests

To add new stress test scenarios:

1. Create test files in `tests/stress/`
2. Use the `@pytest.mark.stress` decorator
3. Use utilities from `tests/stress/test_utils.py`
4. Follow the existing naming conventions

Example:
```python
@pytest.mark.stress
def test_my_stress_scenario():
    # Your stress test implementation
    pass
```

### Environment Configuration

For advanced scenarios, you can set environment variables:

```bash
export VES_STRESS_LARGE_FILE_SIZE_MB=100  # Customize max file size
export VES_STRESS_MAX_FILES=2000          # Customize max file count
export VES_STRESS_TEMP_DIR=/fast/storage  # Use faster storage
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Stress Tests
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:     # Manual trigger

jobs:
  stress-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run stress tests
        run: |
          docker compose run --rm vestigium-stress
```

### Performance Monitoring

To track performance over time:

```bash
# Save results with timestamp (override command for custom output)
docker compose run --rm vestigium-stress python -m pytest tests/stress/ -v -m stress 2>&1 | tee "stress_results_$(date +%Y%m%d_%H%M%S).log"
```

## Troubleshooting

### Common Issues

**"Tests taking too long"**:
- The default configuration runs all tests; this is expected for stress testing
- Check system resources (CPU, memory, disk I/O)
- For quicker testing, override with: `docker compose run --rm vestigium-stress python -m pytest tests/stress/ -m stress -k "not (50mb or 100mb or 1000)"`

**"Out of disk space"**:
- Stress tests create temporary large files
- Ensure at least 1GB free space
- Temporary files are cleaned up automatically

**"Docker container issues"**:
- Update Docker and docker-compose
- Increase Docker memory limits if needed
- Check Docker daemon status

**"Inconsistent results"**:
- Performance can vary based on system load
- Run tests multiple times for baseline
- Docker provides more consistent environment than local execution

### Getting Help

If you encounter issues with stress tests:

1. Check this documentation first
2. The default command runs all stress tests as configured
3. For detailed output, override the command: `docker compose run --rm vestigium-stress python -m pytest tests/stress/ -v -m stress`
4. Check system resources and available disk space
5. Review the test logs for specific error messages

For performance questions or unexpected results, consider:
- Your hardware specifications
- Other running processes
- Storage type (SSD vs HDD)
- Available system memory