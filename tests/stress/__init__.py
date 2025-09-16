"""
Stress tests for Vestigium VCS.

This module contains performance stress tests designed to evaluate how Vestigium
handles large files, numerous files, and complex repository operations under load.

These tests are separate from unit tests and are designed to:
- Test performance with large files (1MB+)
- Test performance with many files (100+ files)
- Measure memory usage and execution time
- Identify performance bottlenecks

Run these tests with: pytest tests/stress/ -m stress -v
"""