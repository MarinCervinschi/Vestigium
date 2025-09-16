"""
Stress tests for handling numerous files in Vestigium VCS.

These tests evaluate how Vestigium performs when handling many files,
testing operations like add, commit, and status with hundreds or thousands of files.
"""

import time
import tempfile
import shutil
from pathlib import Path
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any

import pytest

from src.commands.add import add
from src.commands.commit import commit_create
from src.commands.status import cmd_status
from src.core.repository import repo_create
from src.core.index import index_read
from src.utils.tree import tree_from_index
from tests.stress.test_utils import (
    create_many_small_files,
    create_deep_directory_structure,
    create_binary_files,
)
from datetime import datetime


@pytest.mark.stress
class TestManyFiles:
    """Test performance with many files."""

    def setup_method(self):
        """Set up test environment for each test."""
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

    def teardown_method(self):
        """Clean up after each test."""
        import os

        os.chdir(self.original_cwd)

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def measure_operation_time(self, operation_func, *args, **kwargs) -> Dict[str, Any]:
        """
        Measure the execution time of an operation.

        Returns:
            Dictionary with timing information
        """
        start_time = time.time()
        # Capture and suppress output from the operation
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = operation_func(*args, **kwargs)
        end_time = time.time()

        return {"result": result, "execution_time": end_time - start_time}

    @pytest.mark.parametrize("num_files", [50, 100, 500, 1000])
    def test_add_many_small_files(self, num_files):
        """Test adding many small files."""
        # Create many small files
        files_dir = self.repo_dir / "many_files"
        created_files = create_many_small_files(files_dir, num_files, 1024)
        self.created_files.extend(created_files)

        # Get relative paths for adding
        relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]

        # Measure add operation
        metrics = self.measure_operation_time(add, self.repo, relative_paths)

        # Verify all files were added to index
        index = index_read(self.repo)
        index_names = {entry.name for entry in index.entries}
        for path in relative_paths:
            assert path in index_names, f"File {path} not found in index"

        # Performance assertions (adjust based on requirements)
        files_per_second = num_files / metrics["execution_time"]
        if num_files <= 100:
            assert (
                files_per_second > 20
            ), f"Add rate too slow: {files_per_second:.2f} files/second"
        else:
            assert (
                files_per_second > 10
            ), f"Add rate too slow: {files_per_second:.2f} files/second"

    @pytest.mark.parametrize("num_files", [50, 200, 500])
    def test_commit_many_files(self, num_files):
        """Test committing many files."""
        # Create and add many files
        files_dir = self.repo_dir / "commit_many"
        created_files = create_many_small_files(files_dir, num_files, 512)
        self.created_files.extend(created_files)

        relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]
        add(self.repo, relative_paths)

        # Measure commit operation
        index = index_read(self.repo)
        tree_sha = tree_from_index(self.repo, index)

        metrics = self.measure_operation_time(
            commit_create,
            self.repo,
            tree_sha,
            None,  # No parent commit
            "Test User <test@example.com>",  # Correct author format
            datetime.now(),
            f"Add {num_files} files",
        )

        # Verify commit was created
        commit_sha = metrics["result"]
        assert commit_sha is not None
        assert len(commit_sha) == 40

        # Performance assertions
        assert (
            metrics["execution_time"] < 30.0
        ), f"Commit operation took too long: {metrics['execution_time']:.2f}s"

    @pytest.mark.parametrize(
        "depth,files_per_level",
        [
            (5, 5),  # 5 levels, 5 files each
            (10, 3),  # 10 levels, 3 files each
            (3, 10),  # 3 levels, 10 files each
        ],
    )
    def test_deep_directory_structure(self, depth, files_per_level):
        """Test adding files in deep directory structures."""
        # Create deep directory structure
        deep_dir = self.repo_dir / "deep_structure"
        created_files = create_deep_directory_structure(
            deep_dir, depth, files_per_level
        )
        self.created_files.extend(created_files)

        relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]

        # Measure add operation
        metrics = self.measure_operation_time(add, self.repo, relative_paths)

        # Verify all files were added
        index = index_read(self.repo)
        index_names = {entry.name for entry in index.entries}
        for path in relative_paths:
            assert path in index_names

        # Performance should not degrade significantly with depth
        assert (
            metrics["execution_time"] < 15.0
        ), f"Deep directory add took too long: {metrics['execution_time']:.2f}s"

    @pytest.mark.parametrize("num_files", [50, 100, 200])
    def test_binary_files_performance(self, num_files):
        """Test performance with binary files."""
        # Create binary files
        binary_dir = self.repo_dir / "binary_files"
        created_files = create_binary_files(binary_dir, num_files)
        self.created_files.extend(created_files)

        relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]

        # Measure add operation
        metrics = self.measure_operation_time(add, self.repo, relative_paths)

        # Verify all files were added
        index = index_read(self.repo)
        assert len(index.entries) == num_files

        # Binary files should not be significantly slower than text files
        files_per_second = num_files / metrics["execution_time"]
        assert (
            files_per_second > 15
        ), f"Binary file add rate too slow: {files_per_second:.2f} files/second"

    def test_incremental_adds(self):
        """Test performance of incremental file additions."""
        timing_data = []

        # Add files incrementally in batches
        batch_sizes = [10, 25, 50, 100]
        total_files = 0

        for batch_size in batch_sizes:
            # Create batch of files
            batch_dir = self.repo_dir / f"batch_{batch_size}"
            created_files = create_many_small_files(batch_dir, batch_size, 512)
            self.created_files.extend(created_files)

            relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]

            # Measure add operation
            metrics = self.measure_operation_time(add, self.repo, relative_paths)

            total_files += batch_size
            timing_data.append(
                {
                    "batch_size": batch_size,
                    "total_files": total_files,
                    "execution_time": metrics["execution_time"],
                    "files_per_second": batch_size / metrics["execution_time"],
                }
            )

        # Performance should remain relatively consistent
        rates = [data["files_per_second"] for data in timing_data]
        min_rate = min(rates)
        max_rate = max(rates)

        # Rate shouldn't degrade by more than 50%
        assert (
            min_rate > max_rate * 0.5
        ), f"Performance degraded too much: {min_rate:.2f} vs {max_rate:.2f}"

    def test_status_with_many_files(self):
        """Test status command performance with many files."""
        # Create many files and add them
        num_files = 200
        files_dir = self.repo_dir / "status_test"
        created_files = create_many_small_files(files_dir, num_files, 256)
        self.created_files.extend(created_files)

        relative_paths = [str(f.relative_to(self.repo_dir)) for f in created_files]
        add(self.repo, relative_paths)

        # Measure status operation
        metrics = self.measure_operation_time(cmd_status, type("Args", (), {})())

        # Status should be reasonably fast
        assert (
            metrics["execution_time"] < 5.0
        ), f"Status operation took too long: {metrics['execution_time']:.2f}s"

    def test_mixed_file_operations(self):
        """Test mixed operations with various file types and sizes."""
        # Create a mix of different files
        small_files = create_many_small_files(self.repo_dir / "small", 50, 256)
        medium_files = create_many_small_files(self.repo_dir / "medium", 20, 4096)
        binary_files = create_binary_files(self.repo_dir / "binary", 30)

        all_files = small_files + medium_files + binary_files
        self.created_files.extend(all_files)

        relative_paths = [str(f.relative_to(self.repo_dir)) for f in all_files]

        # Measure combined operations
        add_metrics = self.measure_operation_time(add, self.repo, relative_paths)

        index = index_read(self.repo)
        tree_sha = tree_from_index(self.repo, index)

        commit_metrics = self.measure_operation_time(
            commit_create,
            self.repo,
            tree_sha,
            None,
            "Test User <test@example.com>",  # Correct author format
            datetime.now(),
            "Mixed file types commit",
        )

        # Overall performance should be reasonable
        total_time = add_metrics["execution_time"] + commit_metrics["execution_time"]
        assert (
            total_time < 20.0
        ), f"Combined operations took too long: {total_time:.2f}s"
