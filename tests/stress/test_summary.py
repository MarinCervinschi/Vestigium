"""
Performance summary test for Vestigium VCS.

This test runs last and provides a comprehensive performance summary
that can be used to update documentation with current performance metrics.
"""

import time
import tempfile
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Dict, Any

import pytest

from src.commands.add import add
from src.commands.status import cmd_status
from src.core.repository import repo_create
from tests.stress.test_utils import create_large_file, create_many_small_files


@pytest.mark.stress
class TestPerformanceSummary:
    """Final performance summary for Vestigium VCS."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.repo_dir = self.test_dir / "test_repo"
        self.repo_dir.mkdir()

        # Initialize repository
        self.repo = repo_create(str(self.repo_dir))

        # Change to repo directory for commands
        self.original_cwd = Path.cwd()
        import os

        os.chdir(self.repo_dir)

        self.created_files = []
        self.performance_data = []

    def teardown_method(self):
        """Clean up after each test."""
        import os

        os.chdir(self.original_cwd)

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def measure_operation_time(self, operation_func, *args, **kwargs) -> Dict[str, Any]:
        """Measure the execution time of an operation with output suppressed."""
        start_time = time.time()

        # Capture and suppress output from the operation
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = operation_func(*args, **kwargs)

        end_time = time.time()

        return {"result": result, "execution_time": end_time - start_time}

    def test_vestigium_performance_summary(self):
        """Comprehensive performance test with final summary."""

        # Test 1: Large file performance
        large_file_results = []
        for size_mb in [1, 10, 25, 50]:
            large_file = self.repo_dir / f"perf_test_{size_mb}mb.txt"
            create_large_file(large_file, size_mb)
            self.created_files.append(large_file)

            metrics = self.measure_operation_time(
                add, self.repo, [str(large_file.relative_to(self.repo_dir))]
            )

            throughput = size_mb / metrics["execution_time"]
            large_file_results.append(
                {
                    "size_mb": size_mb,
                    "throughput_mbps": throughput,
                    "time": metrics["execution_time"],
                }
            )

        # Test 2: Many files performance
        many_files_results = []
        for num_files in [100, 500]:
            files_dir = self.repo_dir / f"many_files_{num_files}"
            created_files = create_many_small_files(files_dir, num_files, 1024)
            self.created_files.extend(created_files)

            relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]

            metrics = self.measure_operation_time(add, self.repo, relative_paths)

            files_per_sec = num_files / metrics["execution_time"]
            many_files_results.append(
                {
                    "num_files": num_files,
                    "files_per_sec": files_per_sec,
                    "time": metrics["execution_time"],
                }
            )

        # Test 3: Status performance
        status_metrics = self.measure_operation_time(cmd_status, type("Args", (), {})())
        status_ops_per_sec = 1 / status_metrics["execution_time"]

        print("\n" + "=" * 60)
        print("🚀 VESTIGIUM VCS PERFORMANCE SUMMARY")
        print("=" * 60)

        print("\n📁 Large File Performance:")
        for result in large_file_results:
            print(
                f"   {result['size_mb']:2d}MB files: {result['throughput_mbps']:6.1f} MB/s ({result['time']:4.2f}s)"
            )

        best_large_throughput = max(r["throughput_mbps"] for r in large_file_results)
        avg_large_throughput = sum(
            r["throughput_mbps"] for r in large_file_results
        ) / len(large_file_results)

        print("\n📦 Many Files Performance:")
        for result in many_files_results:
            print(
                f"   {result['num_files']:3d} files: {result['files_per_sec']:6.1f} files/s ({result['time']:4.2f}s)"
            )

        best_files_rate = max(r["files_per_sec"] for r in many_files_results)
        avg_files_rate = sum(r["files_per_sec"] for r in many_files_results) / len(
            many_files_results
        )

        print(
            f"\n📊 Status Performance: {status_ops_per_sec:.1f} ops/s ({status_metrics['execution_time']:.2f}s)"
        )

        print("\n🎯 SUMMARY FOR DOCUMENTATION:")
        print(
            f"   • Large files: {avg_large_throughput:.1f} MB/s avg, {best_large_throughput:.1f} MB/s peak"
        )
        print(
            f"   • Many files: {avg_files_rate:.0f} files/s avg, {best_files_rate:.0f} files/s peak"
        )
        print(f"   • Status ops: {status_ops_per_sec:.1f} ops/s")

        print("=" * 60 + "\n")

        # Assertions to ensure reasonable performance
        assert (
            avg_large_throughput > 5.0
        ), f"Large file throughput too low: {avg_large_throughput:.1f} MB/s"
        assert (
            avg_files_rate > 50.0
        ), f"Files rate too low: {avg_files_rate:.1f} files/s"
        assert (
            status_ops_per_sec > 1.0
        ), f"Status too slow: {status_ops_per_sec:.1f} ops/s"
