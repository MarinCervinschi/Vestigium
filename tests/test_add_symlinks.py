import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.commit import cmd_commit
from src.commands.init import cmd_init
from src.core.index import index_read
from src.core.repository import repo_find


class TestAddSymlinks:
    """Test cases for adding symlinks to the repository."""

    def test_add_symlink_to_file(self, temp_dir, clean_env):
        """Test adding a symlink that points to a regular file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create target file
        target_file = repo_path / "target.txt"
        target_file.write_text("Target file content")

        # Create symlink pointing to the target file
        symlink_path = repo_path / "link.txt"
        symlink_path.symlink_to("target.txt")

        # Add both files to the index
        add_args = Namespace(path=["target.txt", "link.txt"])
        cmd_add(add_args)

        # Verify both entries are in the index
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        # Find entries
        target_entry = None
        symlink_entry = None
        for entry in index.entries:
            if entry.name == "target.txt":
                target_entry = entry
            elif entry.name == "link.txt":
                symlink_entry = entry

        # Verify target file entry
        assert target_entry is not None
        assert target_entry.mode_type == 0b1000  # Regular file
        assert target_entry.mode_perms == 0o644

        # Verify symlink entry
        assert symlink_entry is not None
        assert symlink_entry.mode_type == 0b1010  # Symlink
        assert symlink_entry.mode_perms == 0o000  # No permissions for symlinks

        # Verify that the symlink SHA is different from target SHA
        # (symlink stores the path, not the content)
        assert target_entry.sha != symlink_entry.sha

    def test_add_broken_symlink(self, temp_dir, clean_env):
        """Test adding a symlink that points to a non-existent file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create symlink pointing to non-existent file
        broken_symlink_path = repo_path / "broken_link.txt"
        broken_symlink_path.symlink_to("nonexistent.txt")

        # Add broken symlink to the index
        add_args = Namespace(path=["broken_link.txt"])
        cmd_add(add_args)

        # Verify symlink entry is in the index
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        symlink_entry = None
        for entry in index.entries:
            if entry.name == "broken_link.txt":
                symlink_entry = entry
                break

        assert symlink_entry is not None
        assert symlink_entry.mode_type == 0b1010  # Symlink
        assert symlink_entry.mode_perms == 0o000

    def test_add_relative_symlink(self, temp_dir, clean_env):
        """Test adding a symlink with a relative path."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create subdirectory with target file
        subdir = repo_path / "subdir"
        subdir.mkdir()
        target_file = subdir / "target.txt"
        target_file.write_text("Target in subdirectory")

        # Create relative symlink from root to subdirectory file
        rel_symlink_path = repo_path / "rel_link.txt"
        rel_symlink_path.symlink_to("subdir/target.txt")

        # Add symlink to the index
        add_args = Namespace(path=["rel_link.txt"])
        cmd_add(add_args)

        # Verify symlink entry
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        symlink_entry = None
        for entry in index.entries:
            if entry.name == "rel_link.txt":
                symlink_entry = entry
                break

        assert symlink_entry is not None
        assert symlink_entry.mode_type == 0b1010  # Symlink

    def test_add_absolute_symlink(self, temp_dir, clean_env):
        """Test adding a symlink with an absolute path."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create symlink with absolute path
        abs_symlink_path = repo_path / "abs_link.txt"
        abs_symlink_path.symlink_to("/tmp/some_file.txt")

        # Add symlink to the index
        add_args = Namespace(path=["abs_link.txt"])
        cmd_add(add_args)

        # Verify symlink entry
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        symlink_entry = None
        for entry in index.entries:
            if entry.name == "abs_link.txt":
                symlink_entry = entry
                break

        assert symlink_entry is not None
        assert symlink_entry.mode_type == 0b1010  # Symlink

    def test_add_symlink_and_commit_checkout(self, temp_dir, clean_env):
        """Test full workflow: add symlink, commit, and checkout."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create target file and symlink
        target_file = repo_path / "target.txt"
        target_file.write_text("Content for symlink test")

        symlink_path = repo_path / "link.txt"
        symlink_path.symlink_to("target.txt")

        # Add and commit
        add_args = Namespace(path=["target.txt", "link.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add file and symlink")
        cmd_commit(commit_args)

        # Now test checkout (the symlink should be recreated properly)
        from src.commands.checkout import cmd_checkout
        from src.core.objects import object_find

        repo = repo_find()
        assert repo is not None
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None

        # Create destination directory
        dest_dir = Path(temp_dir) / "checkout_test"

        # Checkout
        checkout_args = Namespace(commit=head_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify files and symlink were checked out correctly
        assert (dest_dir / "target.txt").exists()
        assert (dest_dir / "target.txt").is_file()
        assert (dest_dir / "target.txt").read_text() == "Content for symlink test"

        assert (dest_dir / "link.txt").exists()
        assert (dest_dir / "link.txt").is_symlink()
        assert os.readlink(dest_dir / "link.txt") == "target.txt"

        # Verify symlink functionality
        assert (dest_dir / "link.txt").read_text() == "Content for symlink test"

    def test_add_directory_symlink_fails(self, temp_dir, clean_env):
        """Test that adding a symlink to a directory fails appropriately."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create directory and symlink to it
        test_dir = repo_path / "test_dir"
        test_dir.mkdir()

        dir_symlink_path = repo_path / "dir_link"
        dir_symlink_path.symlink_to("test_dir")

        # Adding directory symlink should still work (Git supports this)
        add_args = Namespace(path=["dir_link"])
        cmd_add(add_args)

        # Verify it was added as a symlink
        repo = repo_find()
        assert repo is not None
        index = index_read(repo)

        symlink_entry = None
        for entry in index.entries:
            if entry.name == "dir_link":
                symlink_entry = entry
                break

        assert symlink_entry is not None
        assert symlink_entry.mode_type == 0b1010  # Symlink

    def test_add_invalid_path_fails(self, temp_dir, clean_env):
        """Test that adding non-existent paths still fails."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Try to add non-existent file
        add_args = Namespace(path=["nonexistent.txt"])

        with pytest.raises(Exception, match="Not a file or symlink"):
            cmd_add(add_args)

    def test_symlink_mode_in_tree(self, temp_dir, clean_env):
        """Test that symlinks get the correct mode (120000) in tree objects."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create symlink
        symlink_path = repo_path / "test_link.txt"
        symlink_path.symlink_to("target.txt")

        # Add and commit
        add_args = Namespace(path=["test_link.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add symlink")
        cmd_commit(commit_args)

        # Check the tree object to verify mode
        from src.core.objects import VesCommit, VesTree, object_find, object_read

        repo = repo_find()
        assert repo is not None
        
        head_sha = object_find(repo, "HEAD")
        assert head_sha is not None
        
        commit_obj = object_read(repo, head_sha)
        assert isinstance(commit_obj, VesCommit)
        
        tree_sha = commit_obj.kvlm[b"tree"].decode("ascii")
        tree_obj = object_read(repo, tree_sha)
        assert isinstance(tree_obj, VesTree)

        # Find the symlink entry in the tree
        symlink_tree_entry = None
        for item in tree_obj.items:
            if item.path == "test_link.txt":
                symlink_tree_entry = item
                break

        assert symlink_tree_entry is not None
        # Verify the mode is 120000 (symlink mode in Git)
        assert symlink_tree_entry.mode == b"120000"