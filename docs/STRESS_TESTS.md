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

### Current Performance Results

Based on the latest stress test runs, here are Vestigium's current performance metrics:

```
============================================================
🚀 VESTIGIUM VCS PERFORMANCE SUMMARY
============================================================

📁 Large File Performance:
    1MB files:   30.6 MB/s (0.03s)
   10MB files:   31.8 MB/s (0.31s)
   25MB files:   31.6 MB/s (0.79s)
   50MB files:   31.2 MB/s (1.60s)

📦 Many Files Performance:
   100 files: 15,655 files/s (0.01s)
   500 files: 17,382 files/s (0.03s)

📊 Status Performance: 91.8 ops/s (0.01s)

🎯 SUMMARY FOR DOCUMENTATION:
   • Large files: 31.3 MB/s avg, 31.8 MB/s peak
   • Many files: 16,519 files/s avg, 17,382 files/s peak
   • Status ops: 91.8 ops/s
============================================================
```

### Computational Complexity Analysis

The most computationally intensive operations in Vestigium are:

#### 1. **File Hashing (`ves add`)**

- **Complexity**: O(file_size) - Linear with file content
- **Bottleneck**: SHA-1 computation on entire file content
- **Testing approach**: Files from 1MB to 50MB to measure throughput degradation
- **Good values**: > 25 MB/s for consistent performance
- **Current performance**: **31.3 MB/s average** ✅ Excellent

#### 2. **Index Operations (Many Files)**

- **Complexity**: O(n log n) - Due to file sorting and tree operations
- **Bottleneck**: File system traversal and index updates
- **Testing approach**: Batches from 100 to 500+ files to measure scaling
- **Good values**: > 1,000 files/s for batch operations
- **Current performance**: **16,519 files/s average** ✅ Excellent

#### 3. **Tree Construction (`ves commit`)**

- **Complexity**: O(n) where n = number of staged files
- **Bottleneck**: Building directory tree structure and computing tree hashes
- **Testing approach**: Commits with varying numbers of files and directory depths
- **Good values**: Commit time should scale linearly with file count
- **Current performance**: Scales well with file count

#### 4. **Status Checking (`ves status`)**

- **Complexity**: O(n) where n = number of tracked files
- **Bottleneck**: Comparing working directory with index (stat calls + hash comparison)
- **Testing approach**: Repositories with hundreds of tracked files
- **Good values**: > 10 ops/s regardless of repository size
- **Current performance**: **91.8 ops/s** ✅ Excellent

### Performance Analysis

**Strengths**:

- **File processing**: Vestigium maintains consistent ~31 MB/s throughput even for large files
- **Batch operations**: Excellent scalability with 16k+ files/s for many-file operations
- **Status operations**: Very fast repository state checking at 91+ ops/s

**Scalability characteristics**:

- Large files: Linear scaling with minimal overhead (30.6-31.8 MB/s range)
- Many files: Super-linear performance improvement with batch size
- Memory usage: Efficient memory management across all test scenarios

### Performance Expectations

Based on typical hardware and current Vestigium performance, here are the expectations:

**Large Files** (Current: 31.3 MB/s avg):

- Target: > 25 MB/s consistently
- 1-10MB files: < 1 second per add operation
- 25-50MB files: < 2 seconds per add operation
- Commit operations: Should scale linearly with file size

**Many Files** (Current: 16,519 files/s avg):

- Target: > 1,000 files/s for batch operations
- 100+ files: > 10,000 files/s preferred
- 500+ files: > 5,000 files/s acceptable
- Deep structures: Should not significantly impact performance

**Status Operations** (Current: 91.8 ops/s):

- Target: > 10 ops/s regardless of repository size
- Large repositories: < 0.5 seconds for status check
- Should remain fast even with hundreds of tracked files

### Interpreting Failures

Common reasons for test failures:

1. **Timeout**: Operation took longer than expected

   - Check available disk I/O performance
   - Verify sufficient RAM is available

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

### Performance Monitoring

To track performance over time:

```bash
# Save results with timestamp (override command for custom output)
docker compose run --rm vestigium-stress 2>&1 | tee "logs/stress_$(date +%Y%m%d_%H%M%S).log"
```
