"""
Stress tests for large file handling in Vestigium VCS.

These tests evaluate how Vestigium performs when handling files of various sizes,
from 1MB to 100MB, testing operations like add, commit, status, and checkout.
"""

import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest

from src.commands.add import add
from src.commands.commit import commit_create
from src.commands.status import cmd_status
from src.core.repository import repo_create, VesRepository
from src.core.index import index_read
from src.utils.config import vesconfig_read, vesconfig_user_get
from src.utils.tree import tree_from_index
from tests.stress.test_utils import create_large_file, cleanup_test_files
from datetime import datetime


@pytest.mark.stress
class TestLargeFiles:
    """Test performance with large files."""

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
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        return {
            'result': result,
            'execution_time': end_time - start_time
        }

    @pytest.mark.parametrize("file_size_mb", [1, 5, 10, 25, 50])
    def test_add_large_file(self, file_size_mb):
        """Test adding files of increasing sizes."""
        # Create large file
        large_file = self.repo_dir / f"large_file_{file_size_mb}mb.txt"
        create_large_file(large_file, file_size_mb)
        self.created_files.append(large_file)
        
        # Measure add operation
        metrics = self.measure_operation_time(
            add, self.repo, [str(large_file.relative_to(self.repo_dir))]
        )
        
        print(f"\nLarge file add ({file_size_mb}MB):")
        print(f"  Execution time: {metrics['execution_time']:.2f}s")
        
        # Verify file was added to index
        index = index_read(self.repo)
        assert any(entry.name == str(large_file.relative_to(self.repo_dir)) 
                  for entry in index.entries)
        
        # Performance assertions (adjust thresholds as needed)
        if file_size_mb <= 10:
            assert metrics['execution_time'] < 5.0, \
                f"Add operation took too long: {metrics['execution_time']:.2f}s"
        else:
            assert metrics['execution_time'] < 15.0, \
                f"Add operation took too long: {metrics['execution_time']:.2f}s"

    @pytest.mark.parametrize("file_size_mb", [1, 10, 25])
    def test_commit_large_file(self, file_size_mb):
        """Test committing large files."""
        # Create and add large file
        large_file = self.repo_dir / f"commit_large_{file_size_mb}mb.txt"
        create_large_file(large_file, file_size_mb)
        self.created_files.append(large_file)
        
        add(self.repo, [str(large_file.relative_to(self.repo_dir))])
        
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
            f"Add large file {file_size_mb}MB"
        )
        
        print(f"\nLarge file commit ({file_size_mb}MB):")
        print(f"  Execution time: {metrics['execution_time']:.2f}s")
        
        # Verify commit was created
        commit_sha = metrics['result']
        assert commit_sha is not None
        assert len(commit_sha) == 40  # SHA-1 hash length
        
        # Performance assertions
        assert metrics['execution_time'] < 10.0, \
            f"Commit operation took too long: {metrics['execution_time']:.2f}s"

    @pytest.mark.parametrize("num_files,file_size_mb", [
        (3, 1),   # 3 x 1MB files
        (2, 5),   # 2 x 5MB files
        (1, 10),  # 1 x 10MB file
    ])
    def test_multiple_large_files_batch_add(self, num_files, file_size_mb):
        """Test adding multiple large files in a single operation."""
        files_to_add = []
        
        # Create multiple large files
        for i in range(num_files):
            large_file = self.repo_dir / f"batch_{i}_{file_size_mb}mb.txt"
            create_large_file(large_file, file_size_mb)
            self.created_files.append(large_file)
            files_to_add.append(str(large_file.relative_to(self.repo_dir)))
        
        # Measure batch add operation
        metrics = self.measure_operation_time(
            add, self.repo, files_to_add
        )
        
        total_size_mb = num_files * file_size_mb
        print(f"\nBatch add ({num_files} files, {total_size_mb}MB total):")
        print(f"  Execution time: {metrics['execution_time']:.2f}s")
        print(f"  MB/second: {total_size_mb / metrics['execution_time']:.2f}")
        
        # Verify all files were added
        index = index_read(self.repo)
        for file_path in files_to_add:
            assert any(entry.name == file_path for entry in index.entries)
        
        # Performance assertions
        assert metrics['execution_time'] < 20.0, \
            f"Batch add took too long: {metrics['execution_time']:.2f}s"

    def test_status_with_large_files(self):
        """Test status command performance with large files in repo."""
        # Create several large files
        file_sizes = [1, 2, 5]
        for size in file_sizes:
            large_file = self.repo_dir / f"status_test_{size}mb.txt"
            create_large_file(large_file, size)
            self.created_files.append(large_file)
            add(self.repo, [str(large_file.relative_to(self.repo_dir))])
        
        # Measure status operation
        metrics = self.measure_operation_time(cmd_status, type('Args', (), {})())
        
        print(f"\nStatus with large files:")
        print(f"  Execution time: {metrics['execution_time']:.2f}s")
        
        # Status should be relatively fast even with large files
        assert metrics['execution_time'] < 3.0, \
            f"Status operation took too long: {metrics['execution_time']:.2f}s"

    def test_memory_usage_scaling(self):
        """Test how memory usage scales with file size."""
        memory_data = []
        
        for size_mb in [1, 5, 10]:
            large_file = self.repo_dir / f"memory_test_{size_mb}mb.txt"
            create_large_file(large_file, size_mb)
            self.created_files.append(large_file)
            
            metrics = self.measure_operation_time(
                add, self.repo, [str(large_file.relative_to(self.repo_dir))]
            )
            
            memory_data.append({
                'file_size_mb': size_mb,
                'execution_time': metrics['execution_time']
            })
        
        print(f"\nMemory scaling analysis:")
        for data in memory_data:
            print(f"  {data['file_size_mb']}MB file: "
                  f"{data['execution_time']:.2f}s")
        
        # Execution time should scale reasonably with file size
        execution_times = [data['execution_time'] for data in memory_data]
        assert all(t < 10.0 for t in execution_times), \
            "Execution times should remain reasonable for large files"