import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.init import cmd_init
from src.commands.ls_tree import cmd_ls_tree, ls_tree
from src.core.objects import VesBlob, VesTree, object_read, object_write
from src.core.repository import repo_find
from src.utils.tree import VesTreeLeaf


class TestLsTreeCommand:
    """Test cases for the ls-tree command."""

    def test_ls_tree_outside_repository(self, temp_dir, clean_env):
        """Test that ls-tree raises exception outside a repository."""
        os.chdir(temp_dir)

        args = Namespace(tree="HEAD", recursive=False)

        with pytest.raises(Exception, match="No ves directory."):
            cmd_ls_tree(args)

    def test_ls_tree_simple_blob(self, temp_dir, clean_env, capsys):
        """Test ls-tree with a simple blob object."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a simple blob
        blob = VesBlob(b"test content")
        blob_sha = object_write(blob, repo)

        # Create a tree with the blob
        tree = VesTree()
        leaf = VesTreeLeaf(mode=b"100644", path="test.txt", sha=blob_sha)
        tree.items.append(leaf)
        tree_sha = object_write(tree, repo)

        # Test ls-tree command
        args = Namespace(tree=tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should show the blob entry
        assert "100644 blob" in output
        assert blob_sha in output
        assert "test.txt" in output

    def test_ls_tree_multiple_entries(self, temp_dir, clean_env, capsys):
        """Test ls-tree with multiple entries in a tree."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create multiple blobs
        blob1 = VesBlob(b"content 1")
        blob1_sha = object_write(blob1, repo)

        blob2 = VesBlob(b"content 2")
        blob2_sha = object_write(blob2, repo)

        blob3 = VesBlob(b"content 3")
        blob3_sha = object_write(blob3, repo)

        # Create a tree with multiple blobs
        tree = VesTree()
        tree.items.append(VesTreeLeaf(mode=b"100644", path="file1.txt", sha=blob1_sha))
        tree.items.append(VesTreeLeaf(mode=b"100644", path="file2.py", sha=blob2_sha))
        tree.items.append(VesTreeLeaf(mode=b"100755", path="script.sh", sha=blob3_sha))
        tree_sha = object_write(tree, repo)

        # Test ls-tree command
        args = Namespace(tree=tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show all entries
        assert "100644 blob" in output
        assert "100755 blob" in output
        assert "file1.txt" in output
        assert "file2.py" in output
        assert "script.sh" in output
        assert blob1_sha in output
        assert blob2_sha in output
        assert blob3_sha in output

    def test_ls_tree_with_subdirectory(self, temp_dir, clean_env, capsys):
        """Test ls-tree with subdirectories (non-recursive)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob for subdirectory
        sub_blob = VesBlob(b"subdirectory content")
        sub_blob_sha = object_write(sub_blob, repo)

        # Create subdirectory tree
        sub_tree = VesTree()
        sub_tree.items.append(
            VesTreeLeaf(mode=b"100644", path="sub_file.txt", sha=sub_blob_sha)
        )
        sub_tree_sha = object_write(sub_tree, repo)

        # Create root blob
        root_blob = VesBlob(b"root content")
        root_blob_sha = object_write(root_blob, repo)

        # Create root tree with subdirectory
        root_tree = VesTree()
        root_tree.items.append(
            VesTreeLeaf(mode=b"100644", path="root.txt", sha=root_blob_sha)
        )
        root_tree.items.append(
            VesTreeLeaf(mode=b"040000", path="subdir", sha=sub_tree_sha)
        )
        root_tree_sha = object_write(root_tree, repo)

        # Test ls-tree command (non-recursive)
        args = Namespace(tree=root_tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show root file and subdirectory
        assert "100644 blob" in output
        assert "040000 tree" in output
        assert "root.txt" in output
        assert "subdir" in output
        assert root_blob_sha in output
        assert sub_tree_sha in output
        # Should NOT show contents of subdirectory
        assert "sub_file.txt" not in output

    def test_ls_tree_recursive(self, temp_dir, clean_env, capsys):
        """Test ls-tree with recursive flag."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create deep directory structure
        deep_blob = VesBlob(b"deep content")
        deep_blob_sha = object_write(deep_blob, repo)

        # Create deepest tree
        deep_tree = VesTree()
        deep_tree.items.append(
            VesTreeLeaf(mode=b"100644", path="deep.txt", sha=deep_blob_sha)
        )
        deep_tree_sha = object_write(deep_tree, repo)

        # Create middle tree
        mid_tree = VesTree()
        mid_tree.items.append(
            VesTreeLeaf(mode=b"040000", path="deep", sha=deep_tree_sha)
        )
        mid_tree_sha = object_write(mid_tree, repo)

        # Create root tree
        root_blob = VesBlob(b"root content")
        root_blob_sha = object_write(root_blob, repo)

        root_tree = VesTree()
        root_tree.items.append(
            VesTreeLeaf(mode=b"100644", path="root.txt", sha=root_blob_sha)
        )
        root_tree.items.append(
            VesTreeLeaf(mode=b"040000", path="middle", sha=mid_tree_sha)
        )
        root_tree_sha = object_write(root_tree, repo)

        # Test recursive ls-tree
        args = Namespace(tree=root_tree_sha, recursive=True)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show all files with their full paths
        assert "root.txt" in output
        assert "middle/deep/deep.txt" in output
        assert deep_blob_sha in output
        assert root_blob_sha in output

    def test_ls_tree_different_file_modes(self, temp_dir, clean_env, capsys):
        """Test ls-tree with different file modes."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create blobs for different file types
        regular_blob = VesBlob(b"regular file")
        regular_sha = object_write(regular_blob, repo)

        executable_blob = VesBlob(b"#!/bin/bash\necho hello")
        executable_sha = object_write(executable_blob, repo)

        symlink_blob = VesBlob(b"../target")
        symlink_sha = object_write(symlink_blob, repo)

        # Create tree with different file modes
        tree = VesTree()
        tree.items.append(
            VesTreeLeaf(mode=b"100644", path="regular.txt", sha=regular_sha)
        )
        tree.items.append(
            VesTreeLeaf(mode=b"100755", path="executable.sh", sha=executable_sha)
        )
        tree.items.append(VesTreeLeaf(mode=b"120000", path="symlink", sha=symlink_sha))
        tree_sha = object_write(tree, repo)

        # Test ls-tree command
        args = Namespace(tree=tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show different modes correctly
        assert "100644 blob" in output
        assert "100755 blob" in output
        assert (
            "120000 blob" in output
        )  # Symlink shows as blob with link target as content
        assert "regular.txt" in output
        assert "executable.sh" in output
        assert "symlink" in output

    def test_ls_tree_invalid_object(self, temp_dir, clean_env, capsys):
        """Test ls-tree with invalid object reference."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Try with non-existent SHA
        fake_sha = "a" * 40
        args = Namespace(tree=fake_sha, recursive=False)

        with pytest.raises(Exception, match=f"No such reference {fake_sha}."):
            cmd_ls_tree(args)

    def test_ls_tree_wrong_object_type(self, temp_dir, clean_env, capsys):
        """Test ls-tree with non-tree object."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob (not a tree)
        blob = VesBlob(b"this is a blob, not a tree")
        blob_sha = object_write(blob, repo)

        # Try to use blob SHA as tree
        args = Namespace(tree=blob_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        # Should handle gracefully (return early)
        assert captured.out == ""

    def test_ls_tree_empty_tree(self, temp_dir, clean_env, capsys):
        """Test ls-tree with empty tree."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create empty tree
        empty_tree = VesTree()
        tree_sha = object_write(empty_tree, repo)

        # Test ls-tree command
        args = Namespace(tree=tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        # Should produce no output for empty tree
        assert captured.out == ""

    def test_ls_tree_function_with_prefix(self, temp_dir, clean_env, capsys):
        """Test ls_tree function with custom prefix."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a simple tree
        blob = VesBlob(b"test content")
        blob_sha = object_write(blob, repo)

        tree = VesTree()
        tree.items.append(VesTreeLeaf(mode=b"100644", path="file.txt", sha=blob_sha))
        tree_sha = object_write(tree, repo)

        # Test ls_tree function with custom prefix
        ls_tree(repo, tree_sha, recursive=False, prefix="custom/prefix")

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should show file with custom prefix
        assert "custom/prefix/file.txt" in output

    def test_ls_tree_with_commit_submodule(self, temp_dir, clean_env, capsys):
        """Test ls-tree with commit object (submodule reference)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a fake commit SHA (we'll just use a fake SHA since creating real commits is complex)
        fake_commit_sha = "b" * 40

        # Create tree with submodule reference
        tree = VesTree()
        tree.items.append(
            VesTreeLeaf(mode=b"160000", path="submodule", sha=fake_commit_sha)
        )
        tree_sha = object_write(tree, repo)

        # Test ls-tree command
        args = Namespace(tree=tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show commit type for submodule
        assert "160000 commit" in output
        assert "submodule" in output
        assert fake_commit_sha in output

    def test_ls_tree_mode_padding(self, temp_dir, clean_env, capsys):
        """Test that ls-tree pads file modes to 6 digits."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create blob with short mode
        blob = VesBlob(b"test")
        blob_sha = object_write(blob, repo)

        # Create tree with 5-digit mode (should be padded to 6)
        tree = VesTree()
        tree.items.append(
            VesTreeLeaf(mode=b"40000", path="dir", sha=blob_sha)
        )  # 5 digits
        tree_sha = object_write(tree, repo)

        # Test ls-tree command
        args = Namespace(tree=tree_sha, recursive=False)
        cmd_ls_tree(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should pad to 6 digits
        assert "040000" in output  # Should be padded with leading zero
