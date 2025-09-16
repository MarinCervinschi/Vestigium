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

    def test_checkout_with_symlinks(self, temp_dir, clean_env):
        """Test that checkout properly handles symlinks.

        This test verifies the symlink support in tree_checkout function,
        specifically the code in lines 149-155 of tree.py that checks for
        mode 12**** and creates symlinks using os.symlink().

        Note: Since the add command doesn't currently support symlinks,
        we test the checkout behavior by creating objects directly.
        """
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a regular file first to have something to commit
        target_file = repo_path / "target.txt"
        target_file.write_text("Target file content")

        # Add and commit the target file
        add_args = Namespace(path=["target.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add target file")
        cmd_commit(commit_args)

        # Now we'll manually create a tree with symlinks to test checkout
        from src.core.objects import VesBlob, VesTree, object_write
        from src.utils.tree import VesTreeLeaf

        repo = repo_find()
        assert repo is not None

        # Create blob for symlink content (the target path)
        symlink_blob = VesBlob()
        symlink_blob.blobdata = b"target.txt"
        symlink_sha = object_write(symlink_blob, repo)

        # Create tree with symlink entry (mode 120000 indicates symlink)
        tree = VesTree()

        # Get the blob SHA for target.txt from the index
        from src.core.index import index_read

        index = index_read(repo)
        target_sha = None
        for entry in index.entries:
            if entry.name == "target.txt":
                target_sha = entry.sha
                break

        if target_sha:
            target_leaf = VesTreeLeaf(mode=b"100644", path="target.txt", sha=target_sha)
            tree.items.append(target_leaf)

        # Add symlink entry with mode 120000
        symlink_leaf = VesTreeLeaf(mode=b"120000", path="link.txt", sha=symlink_sha)
        tree.items.append(symlink_leaf)

        # Write the tree
        tree_sha = object_write(tree, repo)

        # Create destination directory
        dest_dir = Path(temp_dir) / "symlink_checkout"

        # Checkout the tree directly (not a commit)
        checkout_args = Namespace(commit=tree_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify regular file was checked out correctly
        assert (dest_dir / "target.txt").exists()
        assert (dest_dir / "target.txt").is_file()
        assert (dest_dir / "target.txt").read_text() == "Target file content"

        # Verify symlink was checked out as a symlink
        assert (dest_dir / "link.txt").exists()
        assert (dest_dir / "link.txt").is_symlink()
        assert os.readlink(dest_dir / "link.txt") == "target.txt"

        # Verify symlink functionality (can read through it)
        assert (dest_dir / "link.txt").read_text() == "Target file content"

    def test_checkout_with_broken_symlinks(self, temp_dir, clean_env):
        """Test that checkout handles symlinks that point to non-existent targets.

        This tests the robustness of the symlink creation code when the
        symlink target doesn't exist or is not accessible.
        """
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a tree with broken symlinks manually
        from src.core.objects import VesBlob, VesTree, object_write
        from src.utils.tree import VesTreeLeaf

        repo = repo_find()
        assert repo is not None

        # Create blob for broken symlink content
        broken_symlink_blob = VesBlob()
        broken_symlink_blob.blobdata = b"nonexistent.txt"
        broken_symlink_sha = object_write(broken_symlink_blob, repo)

        # Create tree with broken symlink
        tree = VesTree()
        broken_symlink_leaf = VesTreeLeaf(
            mode=b"120000", path="broken_link.txt", sha=broken_symlink_sha
        )
        tree.items.append(broken_symlink_leaf)

        # Write the tree
        tree_sha = object_write(tree, repo)

        # Create destination directory
        dest_dir = Path(temp_dir) / "broken_symlink_checkout"

        # Checkout should succeed even with broken symlinks
        checkout_args = Namespace(commit=tree_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify broken symlink was checked out as a symlink
        # Note: broken symlinks exist as symlinks but .exists() returns False
        # We need to check if the symlink file itself exists in the directory
        symlink_path = dest_dir / "broken_link.txt"
        assert symlink_path.is_symlink()
        assert os.readlink(symlink_path) == "nonexistent.txt"

        # Note: We don't test reading through broken symlinks as that would fail

    def test_checkout_symlink_vs_regular_file_mode(self, temp_dir, clean_env):
        """Test that files with different modes are handled correctly.

        This test ensures that the mode checking logic in tree_checkout
        correctly distinguishes between symlinks (mode 12****) and regular files.
        """
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create regular file first
        regular_file = repo_path / "regular.txt"
        regular_file.write_text("Regular file content")

        # Add and commit the regular file
        add_args = Namespace(path=["regular.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add regular file")
        cmd_commit(commit_args)

        # Create tree manually with both regular file and symlink
        from src.core.index import index_read
        from src.core.objects import VesBlob, VesTree, object_write
        from src.utils.tree import VesTreeLeaf

        repo = repo_find()
        assert repo is not None

        # Get the blob SHA for the regular file
        index = index_read(repo)
        regular_sha = None
        for entry in index.entries:
            if entry.name == "regular.txt":
                regular_sha = entry.sha
                break

        # Create symlink blob
        symlink_blob = VesBlob()
        symlink_blob.blobdata = b"regular.txt"
        symlink_sha = object_write(symlink_blob, repo)

        # Create tree with both regular file and symlink
        tree = VesTree()

        # Add regular file
        if regular_sha:
            regular_leaf = VesTreeLeaf(
                mode=b"100644", path="regular.txt", sha=regular_sha
            )
            tree.items.append(regular_leaf)

        # Add symlink (mode 120000 indicates symlink)
        symlink_leaf = VesTreeLeaf(mode=b"120000", path="symlink.txt", sha=symlink_sha)
        tree.items.append(symlink_leaf)

        # Write the tree
        tree_sha = object_write(tree, repo)

        # Create destination directory
        dest_dir = Path(temp_dir) / "mode_test_checkout"

        # Checkout the tree
        checkout_args = Namespace(commit=tree_sha, path=str(dest_dir))
        cmd_checkout(checkout_args)

        # Verify regular file is a regular file
        assert (dest_dir / "regular.txt").exists()
        assert (dest_dir / "regular.txt").is_file()
        assert not (dest_dir / "regular.txt").is_symlink()
        assert (dest_dir / "regular.txt").read_text() == "Regular file content"

        # Verify symlink is actually a symlink
        symlink_file = dest_dir / "symlink.txt"

        # First check if the symlink was created at all
        assert symlink_file.exists(), "symlink.txt was not created"

        # Check if it's actually a symlink
        assert symlink_file.is_symlink(), "symlink.txt should be a symlink"

        # Note: In Python, a symlink that points to a file can be both is_file() and is_symlink()
        # This is the correct behavior - we just need to verify it's a symlink
        assert os.readlink(symlink_file) == "regular.txt"

        # Verify symlink functionality
        assert symlink_file.read_text() == "Regular file content"
