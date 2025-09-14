import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.init import cmd_init
from src.commands.status import branch_get_active, cmd_status, cmd_status_branch
from src.core.repository import repo_find


class TestStatusCommand:
    """Test cases for the status command."""

    def test_status_outside_repository(self, temp_dir, clean_env):
        """Test that status raises exception outside a repository."""
        os.chdir(temp_dir)

        args = Namespace()

        with pytest.raises(Exception, match="No ves directory."):
            cmd_status(args)

    def test_status_clean_repository(self, temp_dir, clean_env, capsys):
        """Test status in a clean repository with no files."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show branch information
        assert "On branch master" in output
        assert "Changes to be committed:" in output
        assert "Changes not staged for commit:" in output
        assert "Untracked files:" in output

    def test_status_with_staged_file(self, temp_dir, clean_env, capsys):
        """Test status with a file added to the index (staged)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "staged.txt"
        test_file.write_bytes(b"This file is staged")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show the file as added since there's no HEAD yet
        assert "On branch master" in output
        assert "Changes to be committed:" in output
        assert "added:" in output
        assert "staged.txt" in output

    def test_status_with_untracked_file(self, temp_dir, clean_env, capsys):
        """Test status with an untracked file in the working directory."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create an untracked file
        untracked_file = repo_path / "untracked.txt"
        untracked_file.write_bytes(b"This file is untracked")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show the file as untracked
        assert "On branch master" in output
        assert "Untracked files:" in output
        assert "untracked.txt" in output

    def test_status_with_mixed_files(self, temp_dir, clean_env, capsys):
        """Test status with both staged and untracked files."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a staged file
        staged_file = repo_path / "staged.txt"
        staged_file.write_bytes(b"This file is staged")
        add_args = Namespace(path=[str(staged_file)])
        cmd_add(add_args)

        # Create an untracked file
        untracked_file = repo_path / "untracked.txt"
        untracked_file.write_bytes(b"This file is untracked")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show both types of files
        assert "On branch master" in output
        assert "Changes to be committed:" in output
        assert "added:" in output
        assert "staged.txt" in output
        assert "Untracked files:" in output
        assert "untracked.txt" in output

    def test_status_with_subdirectory_files(self, temp_dir, clean_env, capsys):
        """Test status with files in subdirectories."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create subdirectory with files
        subdir = repo_path / "subdir"
        subdir.mkdir()

        staged_file = subdir / "staged.txt"
        staged_file.write_bytes(b"Staged file in subdirectory")
        add_args = Namespace(path=[str(staged_file)])
        cmd_add(add_args)

        untracked_file = subdir / "untracked.txt"
        untracked_file.write_bytes(b"Untracked file in subdirectory")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show files with their paths
        assert "subdir/staged.txt" in output
        assert "subdir/untracked.txt" in output

    def test_branch_get_active_default(self, temp_dir, clean_env):
        """Test branch_get_active with default master branch."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        branch = branch_get_active(repo)
        assert branch == "master"

    def test_branch_get_active_detached_head(self, temp_dir, clean_env):
        """Test branch_get_active behavior when HEAD file contains a hash (detached HEAD simulation)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Simulate detached HEAD by writing a hash directly to HEAD
        head_file = Path(repo.vesdir) / "HEAD"
        fake_hash = "a" * 40
        head_file.write_text(fake_hash)

        branch = branch_get_active(repo)
        assert branch is False

    def test_branch_get_active_missing_head(self, temp_dir, clean_env):
        """Test branch_get_active when HEAD file is missing or unreadable."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Remove HEAD file to simulate error condition
        head_file = Path(repo.vesdir) / "HEAD"
        head_file.unlink()

        branch = branch_get_active(repo)
        assert branch is False

    def test_cmd_status_branch_on_master(self, temp_dir, clean_env, capsys):
        """Test cmd_status_branch output when on master branch."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        cmd_status_branch(repo)

        captured = capsys.readouterr()
        assert "On branch master." in captured.out

    def test_cmd_status_branch_detached_head(self, temp_dir, clean_env, capsys):
        """Test cmd_status_branch output when in detached HEAD state."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Simulate detached HEAD
        head_file = Path(repo.vesdir) / "HEAD"
        fake_hash = "b" * 40
        head_file.write_text(fake_hash)

        cmd_status_branch(repo)

        captured = capsys.readouterr()
        output = captured.out
        assert "HEAD detached at" in output
        # The exact hash shown depends on object_find implementation

    def test_status_multiple_files_same_directory(self, temp_dir, clean_env, capsys):
        """Test status with multiple files in the same directory."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create multiple files
        files_data = {
            "file1.txt": b"Content 1",
            "file2.py": b"print('hello')",
            "file3.md": b"# Header",
        }

        staged_files = []
        for filename, content in files_data.items():
            file_path = repo_path / filename
            file_path.write_bytes(content)
            staged_files.append(str(file_path))

        # Add only some files
        add_args = Namespace(path=staged_files[:2])  # Add first 2 files
        cmd_add(add_args)

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show first 2 as added and last as untracked
        assert "file1.txt" in output
        assert "file2.py" in output
        assert "file3.md" in output

        # Check that staged and untracked are in different sections
        lines = output.split("\n")
        changes_idx = next(
            i for i, line in enumerate(lines) if "Changes to be committed:" in line
        )
        untracked_idx = next(
            i for i, line in enumerate(lines) if "Untracked files:" in line
        )

        # file1.txt and file2.py should appear before untracked section
        # file3.md should appear after untracked section
        for line in lines[changes_idx:untracked_idx]:
            if "file1.txt" in line or "file2.py" in line:
                assert "added:" in line

        for line in lines[untracked_idx:]:
            if "file3.md" in line:
                # Should be in untracked section
                break
        else:
            pytest.fail("file3.md not found in untracked section")

    def test_status_empty_directory_ignored(self, temp_dir, clean_env, capsys):
        """Test that status doesn't show empty directories."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create an empty directory
        empty_dir = repo_path / "empty_dir"
        empty_dir.mkdir()

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Empty directories should not appear in status
        assert "empty_dir" not in output

    def test_status_ignores_vesdir(self, temp_dir, clean_env, capsys):
        """Test that status doesn't show files from .ves directory."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create a file in .ves directory (shouldn't be shown)
        ves_dir = Path(repo_path) / ".ves"
        test_file_in_ves = ves_dir / "test_file"
        test_file_in_ves.write_bytes(b"This should not appear in status")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # .ves files should not appear in status
        assert "test_file" not in output
        assert ".ves" not in output
