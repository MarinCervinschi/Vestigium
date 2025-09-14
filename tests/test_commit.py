import os
from argparse import Namespace
from datetime import datetime
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.commit import cmd_commit, commit_create
from src.commands.init import cmd_init
from src.core.index import index_read
from src.core.objects import VesCommit, object_read
from src.core.refs import ref_resolve
from src.core.repository import repo_find


class TestCommitCommand:
    """Test cases for the commit command."""

    def test_commit_single_file(self, temp_dir, clean_env):
        """Test creating a commit with a single file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Hello, World!")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Create a commit
        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Verify the commit was created
        repo = repo_find()
        assert repo is not None

        # HEAD should now point to a commit
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None
        assert len(commit_sha) == 40  # SHA-1 hash length

        # Read and verify the commit object
        commit_obj = object_read(repo, commit_sha)
        assert isinstance(commit_obj, VesCommit)
        # Use the actual email from .vesconfig
        assert (
            commit_obj.kvlm[b"author"]
            .decode()
            .startswith("Test User <test@vestigium.local>")
        )
        assert (
            commit_obj.kvlm[b"committer"]
            .decode()
            .startswith("Test User <test@vestigium.local>")
        )
        assert commit_obj.kvlm[None].decode().strip() == "Initial commit"
        assert b"tree" in commit_obj.kvlm
        assert b"parent" not in commit_obj.kvlm  # First commit has no parent

    def test_commit_multiple_files(self, temp_dir, clean_env):
        """Test creating a commit with multiple files."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add multiple files
        files = ["file1.txt", "file2.txt", "file3.txt"]
        for filename in files:
            test_file = repo_path / filename
            test_file.write_text(f"Content of {filename}")

        add_args = Namespace(path=files)
        cmd_add(add_args)

        # Create a commit
        commit_args = Namespace(message="Add multiple files")
        cmd_commit(commit_args)

        # Verify the commit was created
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Read and verify the commit object
        commit_obj = object_read(repo, commit_sha)
        assert isinstance(commit_obj, VesCommit)
        assert commit_obj.kvlm[None].decode().strip() == "Add multiple files"

    def test_commit_with_parent(self, temp_dir, clean_env):
        """Test creating a commit that has a parent commit."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create first commit
        test_file1 = repo_path / "file1.txt"
        test_file1.write_text("First file")

        add_args1 = Namespace(path=["file1.txt"])
        cmd_add(add_args1)

        commit_args1 = Namespace(message="First commit")
        cmd_commit(commit_args1)

        repo = repo_find()
        assert repo is not None
        first_commit_sha = ref_resolve(repo, "HEAD")
        assert first_commit_sha is not None

        # Create second commit
        test_file2 = repo_path / "file2.txt"
        test_file2.write_text("Second file")

        add_args2 = Namespace(path=["file2.txt"])
        cmd_add(add_args2)

        commit_args2 = Namespace(message="Second commit")
        cmd_commit(commit_args2)

        # Verify the second commit has the first as parent
        second_commit_sha = ref_resolve(repo, "HEAD")
        assert second_commit_sha is not None
        assert second_commit_sha != first_commit_sha

        commit_obj = object_read(repo, second_commit_sha)
        assert isinstance(commit_obj, VesCommit)
        assert commit_obj.kvlm[b"parent"].decode() == first_commit_sha
        assert commit_obj.kvlm[None].decode().strip() == "Second commit"

    def test_commit_empty_index(self, temp_dir, clean_env):
        """Test that committing with empty index still works."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Try to commit without adding any files
        commit_args = Namespace(message="Empty commit")
        cmd_commit(commit_args)

        # Verify the commit was created
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        commit_obj = object_read(repo, commit_sha)
        assert isinstance(commit_obj, VesCommit)
        assert commit_obj.kvlm[None].decode().strip() == "Empty commit"

    def test_commit_without_repository(self, temp_dir, clean_env):
        """Test that commit command fails when not in a repository."""
        os.chdir(temp_dir)

        # Try to commit without being in a repository
        commit_args = Namespace(message="Should fail")

        with pytest.raises(Exception, match="No ves directory."):
            cmd_commit(commit_args)

    def test_commit_multiline_message(self, temp_dir, clean_env):
        """Test creating a commit with a multiline message."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Hello, World!")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Create a commit with multiline message
        multiline_message = (
            "Short summary\n\nLonger description\nwith multiple lines\nand details."
        )
        commit_args = Namespace(message=multiline_message)
        cmd_commit(commit_args)

        # Verify the commit message
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None
        commit_obj = object_read(repo, commit_sha)

        assert isinstance(commit_obj, VesCommit)
        assert commit_obj.kvlm[None].decode().strip() == multiline_message

    def test_commit_create_function_direct(self, temp_dir, clean_env):
        """Test calling commit_create function directly."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file to get a tree
        test_file = repo_path / "test.txt"
        test_file.write_text("Direct test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        # We need to create a tree first
        from src.utils.tree import tree_from_index

        tree_sha = tree_from_index(repo, index)

        # Call commit_create directly
        commit_sha = commit_create(
            repo=repo,
            tree=tree_sha,
            parent=None,
            author="Direct Test <direct@test.com>",
            timestamp=datetime.now(),
            message="Direct commit test",
        )

        # Verify the commit was created
        assert len(commit_sha) == 40
        commit_obj = object_read(repo, commit_sha)
        assert isinstance(commit_obj, VesCommit)
        assert (
            commit_obj.kvlm[b"author"]
            .decode()
            .startswith("Direct Test <direct@test.com>")
        )
        assert commit_obj.kvlm[None].decode().strip() == "Direct commit test"

    def test_commit_timestamp_format(self, temp_dir, clean_env):
        """Test that commit timestamps are formatted correctly."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Timestamp test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Create a commit
        commit_args = Namespace(message="Timestamp test")
        cmd_commit(commit_args)

        # Verify timestamp format
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None
        commit_obj = object_read(repo, commit_sha)

        assert isinstance(commit_obj, VesCommit)
        author_line = commit_obj.kvlm[b"author"].decode()

        # Check that timestamp and timezone are present
        # Format should be: "Name <email> timestamp +timezone"
        parts = author_line.split()
        assert len(parts) >= 3
        # Last part should be timezone (+HHMM or -HHMM)
        timezone = parts[-1]
        assert timezone.startswith(("+", "-"))
        assert len(timezone) == 5  # +HHMM format

        # Second to last should be timestamp (Unix epoch)
        timestamp = parts[-2]
        assert timestamp.isdigit()

    def test_commit_updates_head(self, temp_dir, clean_env):
        """Test that commit properly updates HEAD reference."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        repo = repo_find()
        assert repo is not None

        # Initially HEAD points to master but master doesn't exist
        initial_head = ref_resolve(repo, "HEAD")
        assert initial_head is None

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("HEAD test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Create a commit
        commit_args = Namespace(message="Update HEAD test")
        cmd_commit(commit_args)

        # Verify HEAD now points to the commit
        updated_head = ref_resolve(repo, "HEAD")
        assert updated_head is not None
        assert len(updated_head) == 40
