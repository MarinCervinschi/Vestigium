import os
import tempfile
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.checkout import cmd_checkout
from src.commands.commit import cmd_commit
from src.commands.init import cmd_init
from src.core.objects import VesCommit, object_find, object_read
from src.core.repository import repo_find


class TestCheckoutCommand:
    """Test cases for the checkout command."""

    def test_checkout_commit_to_empty_directory(self, temp_dir, clean_env):
        """Test checking out a commit to an empty directory."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create some files
        test_file = repo_path / "test.txt"
        test_file.write_text("Hello, World!")

        src_dir = repo_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "main.py"
        src_file.write_text("print('Hello from Python')")

        # Add and commit files
        add_args = Namespace(path=["test.txt", "src/main.py"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create destination directory
        dest_dir = Path(temp_dir) / "checkout_dest"

        # Checkout to destination
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify files were checked out correctly
        assert dest_dir.exists()
        assert (dest_dir / "test.txt").exists()
        assert (dest_dir / "src").exists()
        assert (dest_dir / "src" / "main.py").exists()

        # Verify file contents
        assert (dest_dir / "test.txt").read_text() == "Hello, World!"
        assert (
            dest_dir / "src" / "main.py"
        ).read_text() == "print('Hello from Python')"

    def test_checkout_commit_to_existing_empty_directory(self, temp_dir, clean_env):
        """Test checking out a commit to an existing empty directory."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Test content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Test commit")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create empty destination directory
        dest_dir = Path(temp_dir) / "checkout_dest"
        dest_dir.mkdir()

        # Checkout to existing empty directory
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify file was checked out
        assert (dest_dir / "test.txt").exists()
        assert (dest_dir / "test.txt").read_text() == "Test content"

    def test_checkout_tree_object_directly(self, temp_dir, clean_env):
        """Test checking out a tree object directly (not a commit)."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit files
        test_file = repo_path / "test.txt"
        test_file.write_text("Tree test content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Tree test commit")
        cmd_commit(commit_args)

        # Get the tree SHA from the commit
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        commit_obj = object_read(repo, head_sha)
        assert commit_obj is not None
        assert isinstance(commit_obj, VesCommit)

        tree_sha = commit_obj.kvlm[b"tree"].decode("ascii")

        # Create destination directory
        dest_dir = Path(temp_dir) / "tree_checkout"

        # Checkout tree directly
        checkout_args = Namespace(commit=tree_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify file was checked out
        assert (dest_dir / "test.txt").exists()
        assert (dest_dir / "test.txt").read_text() == "Tree test content"

    def test_checkout_nested_directory_structure(self, temp_dir, clean_env):
        """Test checking out a complex directory structure."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create nested directory structure
        (repo_path / "src" / "utils").mkdir(parents=True)
        (repo_path / "tests" / "unit").mkdir(parents=True)
        (repo_path / "docs").mkdir()

        # Create files in various directories
        files_to_create = [
            ("README.md", "# Project README"),
            ("src/main.py", "def main():\n    pass"),
            ("src/utils/helpers.py", "def helper():\n    return True"),
            ("tests/unit/test_main.py", "def test_main():\n    assert True"),
            ("docs/guide.md", "# User Guide"),
        ]

        for file_path, content in files_to_create:
            full_path = repo_path / file_path
            full_path.write_text(content)

        # Add all files
        file_paths = [file_path for file_path, _ in files_to_create]
        add_args = Namespace(path=file_paths)
        cmd_add(add_args)

        commit_args = Namespace(message="Add nested structure")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create destination directory
        dest_dir = Path(temp_dir) / "nested_checkout"

        # Checkout the structure
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify all files and directories exist
        for file_path, content in files_to_create:
            full_dest_path = dest_dir / file_path
            assert full_dest_path.exists(), f"File {file_path} should exist"
            assert (
                full_dest_path.read_text() == content
            ), f"Content mismatch in {file_path}"

        # Verify directory structure
        assert (dest_dir / "src").is_dir()
        assert (dest_dir / "src" / "utils").is_dir()
        assert (dest_dir / "tests").is_dir()
        assert (dest_dir / "tests" / "unit").is_dir()
        assert (dest_dir / "docs").is_dir()

    def test_checkout_to_non_empty_directory_fails(self, temp_dir, clean_env):
        """Test that checkout fails when destination directory is not empty."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Test content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Test commit")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create non-empty destination directory
        dest_dir = Path(temp_dir) / "non_empty_dest"
        dest_dir.mkdir()
        (dest_dir / "existing_file.txt").write_text("Already exists")

        # Checkout should fail
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))

        with pytest.raises(Exception, match="Not empty"):
            cmd_checkout(checkout_args)

    def test_checkout_to_file_path_fails(self, temp_dir, clean_env):
        """Test that checkout fails when destination path is a file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Test content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Test commit")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create file at destination path
        dest_file = Path(temp_dir) / "dest_file.txt"
        dest_file.write_text("This is a file, not a directory")

        # Checkout should fail
        checkout_args = Namespace(commit=head_sha, path=str(dest_file))

        with pytest.raises(Exception, match="Not a directory"):
            cmd_checkout(checkout_args)

    def test_checkout_nonexistent_commit(self, temp_dir, clean_env):
        """Test checkout with a nonexistent commit SHA."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create destination directory
        dest_dir = Path(temp_dir) / "checkout_dest"

        # Try to checkout nonexistent commit
        fake_sha = "1234567890abcdef1234567890abcdef12345678"
        checkout_args = Namespace(commit=fake_sha, path=str(dest_dir))

        # Should raise if object not found
        with pytest.raises(Exception, match=f"No such reference {fake_sha}."):
            cmd_checkout(checkout_args)

        # Destination should not be created
        assert not dest_dir.exists()

    def test_checkout_without_repository(self, temp_dir, clean_env):
        """Test that checkout fails when not in a repository."""
        os.chdir(temp_dir)

        # Create destination directory
        dest_dir = Path(temp_dir) / "checkout_dest"

        # Try to checkout without repository
        checkout_args = Namespace(commit="HEAD", path=str(dest_dir))

        with pytest.raises(Exception, match="No ves directory."):
            cmd_checkout(checkout_args)

    def test_checkout_empty_repository(self, temp_dir, clean_env):
        """Test checkout in an empty repository (no commits)."""
        os.chdir(temp_dir)

        # Initialize empty repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create destination directory
        dest_dir = Path(temp_dir) / "checkout_dest"

        # Try to checkout HEAD in empty repository
        checkout_args = Namespace(commit="HEAD", path=str(dest_dir))

        # Should return silently when HEAD doesn't exist
        cmd_checkout(checkout_args)

        # Destination should not be created
        assert not dest_dir.exists()

    def test_checkout_binary_files(self, temp_dir, clean_env):
        """Test checking out binary files."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create binary file
        binary_data = bytes([i % 256 for i in range(1000)])
        binary_file = repo_path / "data.bin"
        binary_file.write_bytes(binary_data)

        # Add and commit binary file
        add_args = Namespace(path=["data.bin"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add binary file")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create destination directory
        dest_dir = Path(temp_dir) / "binary_checkout"

        # Checkout binary file
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify binary file was checked out correctly
        assert (dest_dir / "data.bin").exists()
        assert (dest_dir / "data.bin").read_bytes() == binary_data

    def test_checkout_with_reference_name(self, temp_dir, clean_env):
        """Test checkout using reference names instead of SHA."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Reference test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Reference commit")
        cmd_commit(commit_args)

        # Create destination directory
        dest_dir = Path(temp_dir) / "ref_checkout"

        # Checkout using HEAD reference
        checkout_args = Namespace(commit="HEAD", path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify file was checked out
        assert (dest_dir / "test.txt").exists()
        assert (dest_dir / "test.txt").read_text() == "Reference test"

    def test_checkout_preserves_file_permissions(self, temp_dir, clean_env):
        """Test that checkout preserves file permissions (basic test)."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create files with different content types
        regular_file = repo_path / "regular.txt"
        regular_file.write_text("Regular file content")

        # Create what would be an executable (though we can't easily test actual execution permissions)
        script_file = repo_path / "script.sh"
        script_file.write_text("#!/bin/bash\necho 'Hello'")

        # Add and commit files
        add_args = Namespace(path=["regular.txt", "script.sh"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add files with different types")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create destination directory
        dest_dir = Path(temp_dir) / "perm_checkout"

        # Checkout files
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify files exist and have content
        assert (dest_dir / "regular.txt").exists()
        assert (dest_dir / "script.sh").exists()
        assert (dest_dir / "regular.txt").read_text() == "Regular file content"
        assert (dest_dir / "script.sh").read_text() == "#!/bin/bash\necho 'Hello'"
