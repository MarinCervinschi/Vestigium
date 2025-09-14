import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.init import cmd_init
from src.commands.rm import cmd_rm, rm
from src.core.index import index_read
from src.core.repository import repo_find


class TestRmCommand:
    """Test cases for the rm command."""

    def test_rm_outside_repository(self, temp_dir, clean_env):
        """Test that rm raises exception outside a repository."""
        os.chdir(temp_dir)

        args = Namespace(path=["test.txt"])
        
        with pytest.raises(Exception, match="No ves directory."):
            cmd_rm(args)

    def test_rm_single_file(self, temp_dir, clean_env):
        """Test removing a single file from index and filesystem."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "remove_me.txt"
        test_file.write_bytes(b"This file will be removed")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Verify file is in index
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 1
        assert index.entries[0].name == "remove_me.txt"
        assert test_file.exists()

        # Remove the file
        rm_args = Namespace(path=[str(test_file)])
        cmd_rm(rm_args)

        # Verify file is removed from index and filesystem
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 0
        assert not test_file.exists()

    def test_rm_multiple_files(self, temp_dir, clean_env):
        """Test removing multiple files at once."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add multiple test files
        files_to_remove = []
        for i, name in enumerate(["file1.txt", "file2.py", "file3.md"]):
            test_file = repo_path / name
            test_file.write_bytes(f"Content of file {i+1}".encode())
            files_to_remove.append(str(test_file))

        add_args = Namespace(path=files_to_remove)
        cmd_add(add_args)

        # Verify files are in index
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 3

        # Remove all files
        rm_args = Namespace(path=files_to_remove)
        cmd_rm(rm_args)

        # Verify all files are removed
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 0
        for file_path in files_to_remove:
            assert not Path(file_path).exists()

    def test_rm_partial_removal(self, temp_dir, clean_env):
        """Test removing some files while keeping others."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add multiple files
        all_files = []
        for i, name in enumerate(["keep1.txt", "remove1.txt", "keep2.txt", "remove2.txt"]):
            test_file = repo_path / name
            test_file.write_bytes(f"Content of {name}".encode())
            all_files.append(str(test_file))

        add_args = Namespace(path=all_files)
        cmd_add(add_args)

        # Remove only some files
        files_to_remove = [all_files[1], all_files[3]]  # remove1.txt, remove2.txt
        rm_args = Namespace(path=files_to_remove)
        cmd_rm(rm_args)

        # Verify correct files are removed and kept
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 2

        remaining_names = [entry.name for entry in index.entries]
        assert "keep1.txt" in remaining_names
        assert "keep2.txt" in remaining_names
        assert "remove1.txt" not in remaining_names
        assert "remove2.txt" not in remaining_names

        # Check filesystem
        assert (repo_path / "keep1.txt").exists()
        assert (repo_path / "keep2.txt").exists()
        assert not (repo_path / "remove1.txt").exists()
        assert not (repo_path / "remove2.txt").exists()

    def test_rm_file_not_in_index(self, temp_dir, clean_env):
        """Test removing a file that is not in the index."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create a file but don't add it to index
        untracked_file = repo_path / "untracked.txt"
        untracked_file.write_bytes(b"This file is not in index")

        # Try to remove the untracked file
        rm_args = Namespace(path=[str(untracked_file)])
        
        with pytest.raises(Exception, match="Cannot remove paths not in the index"):
            cmd_rm(rm_args)

        # File should still exist
        assert untracked_file.exists()

    def test_rm_file_outside_worktree(self, temp_dir, clean_env):
        """Test removing a file outside the repository worktree."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create a file outside the repository
        outside_file = Path(temp_dir) / "outside.txt"
        outside_file.write_bytes(b"This file is outside the repo")

        # Try to remove the file outside worktree
        rm_args = Namespace(path=[str(outside_file)])
        
        with pytest.raises(Exception, match="Cannot remove paths outside of worktree"):
            cmd_rm(rm_args)

        # File should still exist
        assert outside_file.exists()

    def test_rm_with_relative_paths(self, temp_dir, clean_env):
        """Test removing files using relative paths."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "relative_test.txt"
        test_file.write_bytes(b"Test relative path removal")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Remove using relative path
        rm_args = Namespace(path=["relative_test.txt"])
        cmd_rm(rm_args)

        # Verify file is removed
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 0
        assert not test_file.exists()

    def test_rm_subdirectory_files(self, temp_dir, clean_env):
        """Test removing files in subdirectories."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create subdirectory and files
        subdir = repo_path / "subdir"
        subdir.mkdir()

        root_file = repo_path / "root.txt"
        root_file.write_bytes(b"Root file")

        sub_file = subdir / "sub.txt"
        sub_file.write_bytes(b"Sub file")

        # Add both files
        add_args = Namespace(path=[str(root_file), str(sub_file)])
        cmd_add(add_args)

        # Remove only the subdirectory file
        rm_args = Namespace(path=[str(sub_file)])
        cmd_rm(rm_args)

        # Verify correct file is removed
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 1
        assert index.entries[0].name == "root.txt"

        assert root_file.exists()
        assert not sub_file.exists()

    def test_rm_function_with_delete_false(self, temp_dir, clean_env):
        """Test rm function with delete=False (only remove from index)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "keep_on_disk.txt"
        test_file.write_bytes(b"This file should stay on disk")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Remove from index only (not from filesystem)
        repo = repo_find()
        assert repo is not None
        rm(repo, [str(test_file)], delete=False)

        # Verify file is removed from index but exists on filesystem
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 0
        assert test_file.exists()

    def test_rm_function_with_skip_missing_true(self, temp_dir, clean_env):
        """Test rm function with skip_missing=True."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add one file
        tracked_file = repo_path / "tracked.txt"
        tracked_file.write_bytes(b"This file is tracked")

        add_args = Namespace(path=[str(tracked_file)])
        cmd_add(add_args)

        # Create an untracked file
        untracked_file = repo_path / "untracked.txt"
        untracked_file.write_bytes(b"This file is untracked")

        # Try to remove both files with skip_missing=True
        repo = repo_find()
        assert repo is not None
        rm(repo, [str(tracked_file), str(untracked_file)], skip_missing=True)

        # Verify only tracked file is removed, no exception raised
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 0
        assert not tracked_file.exists()
        assert untracked_file.exists()

    def test_rm_empty_repository(self, temp_dir, clean_env):
        """Test rm in an empty repository (no index yet)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create a file but don't add it
        test_file = repo_path / "test.txt"
        test_file.write_bytes(b"Test content")

        # Try to remove from empty index
        rm_args = Namespace(path=[str(test_file)])
        
        with pytest.raises(Exception, match="Cannot remove paths not in the index"):
            cmd_rm(rm_args)

    def test_rm_nonexistent_file(self, temp_dir, clean_env):
        """Test rm with a file path that doesn't exist."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Try to remove a nonexistent file
        nonexistent_path = str(repo_path / "does_not_exist.txt")
        rm_args = Namespace(path=[nonexistent_path])
        
        with pytest.raises(Exception, match="Cannot remove paths not in the index"):
            cmd_rm(rm_args)

    def test_rm_maintains_other_entries_order(self, temp_dir, clean_env):
        """Test that rm maintains the order of other entries in the index."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create multiple files in specific order
        files = ["a.txt", "b.txt", "c.txt", "d.txt"]
        for i, name in enumerate(files):
            test_file = repo_path / name
            test_file.write_bytes(f"Content {i}".encode())
            # Add files individually to maintain order
            add_args = Namespace(path=[str(test_file)])
            cmd_add(add_args)

        # Remove middle file
        rm_args = Namespace(path=[str(repo_path / "b.txt")])
        cmd_rm(rm_args)

        # Verify order of remaining files
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 3
        
        remaining_names = [entry.name for entry in index.entries]
        assert remaining_names == ["a.txt", "c.txt", "d.txt"]