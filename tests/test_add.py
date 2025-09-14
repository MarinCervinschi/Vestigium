import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import add, cmd_add
from src.commands.init import cmd_init
from src.core.index import index_read
from src.core.repository import repo_find


class TestAddCommand:
    """Test cases for the add command."""

    def test_add_single_file(self, temp_dir, clean_env):
        """Test adding a single file to the repository."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a test file
        test_file = repo_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        # Add the file
        args = Namespace(path=["test.txt"])
        cmd_add(args)

        # Verify the file was added to the index
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.name == "test.txt"
        assert entry.fsize == len(test_content.encode())
        assert entry.mode_type == 0b1000  # Regular file
        assert entry.mode_perms == 0o644
        assert len(entry.sha) == 40  # SHA-1 hash length

    def test_add_multiple_files(self, temp_dir, clean_env):
        """Test adding multiple files to the repository."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create multiple test files
        files = ["file1.txt", "file2.txt", "file3.txt"]
        for filename in files:
            test_file = repo_path / filename
            test_file.write_text(f"Content of {filename}")

        # Add all files
        args = Namespace(path=files)
        cmd_add(args)

        # Verify all files were added to the index
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 3
        entry_names = [entry.name for entry in index.entries]
        for filename in files:
            assert filename in entry_names

    def test_add_file_in_subdirectory(self, temp_dir, clean_env):
        """Test adding a file in a subdirectory."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a subdirectory and file
        subdir = repo_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("Hello from subdirectory")

        # Add the file
        args = Namespace(path=["subdir/test.txt"])
        cmd_add(args)

        # Verify the file was added with correct path
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.name == "subdir/test.txt"

    def test_add_updates_existing_file(self, temp_dir, clean_env):
        """Test that adding an already-tracked file updates its entry."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Original content")

        args = Namespace(path=["test.txt"])
        cmd_add(args)

        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        original_sha = index.entries[0].sha

        # Modify the file and add again
        test_file.write_text("Modified content")
        cmd_add(args)

        # Verify the entry was updated
        index = index_read(repo)
        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.name == "test.txt"
        assert entry.sha != original_sha  # SHA should change

    def test_add_absolute_path(self, temp_dir, clean_env):
        """Test adding a file using absolute path."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Add using absolute path
        args = Namespace(path=[str(test_file.absolute())])
        cmd_add(args)

        # Verify the file was added with relative path
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.name == "test.txt"  # Should be stored as relative path

    def test_add_file_outside_repository(self, temp_dir, clean_env):
        """Test that adding a file outside the repository fails."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file outside the repository
        outside_file = Path(temp_dir) / "outside.txt"
        outside_file.write_text("Outside content")

        # Try to add the outside file
        args = Namespace(path=[str(outside_file)])

        with pytest.raises(Exception, match=f"Cannot remove paths outside of worktree"):
            cmd_add(args)

    def test_add_nonexistent_file(self, temp_dir, clean_env):
        """Test that adding a nonexistent file fails."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Try to add a nonexistent file
        args = Namespace(path=["nonexistent.txt"])

        with pytest.raises(Exception, match="Not a file"):
            cmd_add(args)

    def test_add_directory(self, temp_dir, clean_env):
        """Test that adding a directory fails."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a directory
        test_dir = repo_path / "testdir"
        test_dir.mkdir()

        # Try to add the directory
        args = Namespace(path=["testdir"])

        with pytest.raises(Exception, match="Not a file"):
            cmd_add(args)

    def test_add_without_repository(self, temp_dir, clean_env):
        """Test that add command fails when not in a repository."""
        os.chdir(temp_dir)

        # Create a file but no repository
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")

        args = Namespace(path=["test.txt"])

        with pytest.raises(Exception, match="No ves directory."):
            cmd_add(args)

    def test_add_empty_file(self, temp_dir, clean_env):
        """Test adding an empty file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create an empty file
        test_file = repo_path / "empty.txt"
        test_file.write_text("")

        # Add the empty file
        args = Namespace(path=["empty.txt"])
        cmd_add(args)

        # Verify the file was added
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.name == "empty.txt"
        assert entry.fsize == 0

    def test_add_binary_file(self, temp_dir, clean_env):
        """Test adding a binary file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a binary file
        test_file = repo_path / "binary.bin"
        binary_content = bytes(range(256))
        test_file.write_bytes(binary_content)

        # Add the binary file
        args = Namespace(path=["binary.bin"])
        cmd_add(args)

        # Verify the file was added
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.name == "binary.bin"
        assert entry.fsize == 256

    def test_add_function_direct_call(self, temp_dir, clean_env):
        """Test calling the add function directly."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        repo = repo_find()
        assert repo is not None

        # Create test files
        test_file1 = repo_path / "direct1.txt"
        test_file2 = repo_path / "direct2.txt"
        test_file1.write_text("Direct call test 1")
        test_file2.write_text("Direct call test 2")

        # Call add function directly
        add(repo, ["direct1.txt", "direct2.txt"])

        # Verify files were added
        index = index_read(repo)
        assert len(index.entries) == 2
        entry_names = [entry.name for entry in index.entries]
        assert "direct1.txt" in entry_names
        assert "direct2.txt" in entry_names

    def test_add_preserves_file_permissions(self, temp_dir, clean_env):
        """Test that add preserves file permission information."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Add the file
        args = Namespace(path=["test.txt"])
        cmd_add(args)

        # Verify the file permissions are recorded
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        assert len(index.entries) == 1
        entry = index.entries[0]
        assert entry.mode_type == 0b1000  # Regular file
        assert entry.mode_perms == 0o644  # Standard permissions
        assert entry.uid >= 0
        assert entry.gid >= 0

    def test_add_creates_blob_object(self, temp_dir, clean_env):
        """Test that add creates the corresponding blob object in the repository."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a test file
        test_file = repo_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        # Add the file
        args = Namespace(path=["test.txt"])
        cmd_add(args)

        # Verify the blob object was created
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)
        entry = index.entries[0]

        # The object should exist in the objects directory
        object_dir = Path(repo.vesdir) / "objects" / entry.sha[:2]
        object_file = object_dir / entry.sha[2:]
        assert object_file.exists()
