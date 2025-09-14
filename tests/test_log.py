import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.commit import cmd_commit
from src.commands.init import cmd_init
from src.commands.log import cmd_log, log_graphviz
from src.core.refs import ref_resolve
from src.core.repository import repo_find


class TestLogCommand:
    """Test cases for the log command."""

    def test_log_single_commit(self, temp_dir, clean_env, capsys):
        """Test log output for a repository with a single commit."""
        os.chdir(temp_dir)

        # Initialize repository and create a commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Hello, World!")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Get the commit SHA and run log
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        log_args = Namespace(commit=commit_sha)
        cmd_log(log_args)

        # Verify output
        captured = capsys.readouterr()
        output = captured.out

        assert "digraph veslog{" in output
        assert "node[shape=rect]" in output
        assert f"c_{commit_sha}" in output
        assert "Initial commit" in output
        assert "}" in output

    def test_log_multiple_commits(self, temp_dir, clean_env, capsys):
        """Test log output for a repository with multiple commits."""
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

        # Create second commit
        test_file2 = repo_path / "file2.txt"
        test_file2.write_text("Second file")

        add_args2 = Namespace(path=["file2.txt"])
        cmd_add(add_args2)

        commit_args2 = Namespace(message="Second commit")
        cmd_commit(commit_args2)

        second_commit_sha = ref_resolve(repo, "HEAD")

        # Run log from the latest commit
        log_args = Namespace(commit=second_commit_sha)
        cmd_log(log_args)

        # Verify output contains both commits and relationship
        captured = capsys.readouterr()
        output = captured.out

        assert "digraph veslog{" in output
        assert f"c_{first_commit_sha}" in output
        assert f"c_{second_commit_sha}" in output
        assert "First commit" in output
        assert "Second commit" in output
        assert f"c_{second_commit_sha} -> c_{first_commit_sha};" in output

    def test_log_with_head_reference(self, temp_dir, clean_env, capsys):
        """Test log using HEAD as reference."""
        os.chdir(temp_dir)

        # Initialize repository and create a commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("HEAD test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="HEAD commit test")
        cmd_commit(commit_args)

        # Run log with HEAD reference
        log_args = Namespace(commit="HEAD")
        cmd_log(log_args)

        # Verify output
        captured = capsys.readouterr()
        output = captured.out

        assert "digraph veslog{" in output
        assert "HEAD commit test" in output

    def test_log_multiline_commit_message(self, temp_dir, clean_env, capsys):
        """Test that log shows only first line of multiline commit messages."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Multiline test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Create commit with multiline message
        multiline_message = "Short summary\n\nLonger description\nwith multiple lines"
        commit_args = Namespace(message=multiline_message)
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")

        # Run log
        log_args = Namespace(commit=commit_sha)
        cmd_log(log_args)

        # Verify only first line is shown
        captured = capsys.readouterr()
        output = captured.out

        assert "Short summary" in output
        assert "Longer description" not in output
        assert "with multiple lines" not in output

    def test_log_commit_message_escaping(self, temp_dir, clean_env, capsys):
        """Test that special characters in commit messages are properly escaped."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Escape test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Create commit with special characters
        special_message = 'Fix "quoted" strings and \\backslashes'
        commit_args = Namespace(message=special_message)
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")

        # Run log
        log_args = Namespace(commit=commit_sha)
        cmd_log(log_args)

        # Verify special characters are escaped
        captured = capsys.readouterr()
        output = captured.out

        # Should contain escaped versions
        assert '\\"quoted\\"' in output
        assert "\\\\backslashes" in output

    def test_log_invalid_commit(self, temp_dir, clean_env, capsys):
        """Test log behavior with invalid commit reference."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Try to log with invalid commit
        log_args = Namespace(commit="nonexistent")
        with pytest.raises(Exception, match="No such reference"):
            cmd_log(log_args)

    def test_log_without_repository(self, temp_dir, clean_env):
        """Test that log command fails when not in a repository."""
        os.chdir(temp_dir)

        # Try to run log without repository
        log_args = Namespace(commit="HEAD")

        with pytest.raises(Exception, match="No ves directory."):
            cmd_log(log_args)

    def test_log_graphviz_function_direct(self, temp_dir, clean_env, capsys):
        """Test calling log_graphviz function directly."""
        os.chdir(temp_dir)

        # Initialize repository and create a commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Direct test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Direct log test")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Call log_graphviz directly
        seen = set()
        log_graphviz(repo, commit_sha, seen)

        # Verify output
        captured = capsys.readouterr()
        output = captured.out

        assert f"c_{commit_sha}" in output
        assert "Direct log test" in output
        assert commit_sha in seen

    def test_log_short_sha_format(self, temp_dir, clean_env, capsys):
        """Test that log displays shortened SHA hashes."""
        os.chdir(temp_dir)

        # Initialize repository and create a commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("SHA test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="SHA format test")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Run log
        log_args = Namespace(commit=commit_sha)
        cmd_log(log_args)

        # Verify short SHA is used in labels
        captured = capsys.readouterr()
        output = captured.out

        short_sha = commit_sha[:7]
        assert f"{short_sha}:" in output
        # But full SHA should be used for node names
        assert f"c_{commit_sha}" in output

    def test_log_empty_repository(self, temp_dir, clean_env, capsys):
        """Test log behavior in repository with no commits."""
        os.chdir(temp_dir)

        # Initialize repository but don't create any commits
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Try to log HEAD (which doesn't exist yet)
        log_args = Namespace(commit="HEAD")
        cmd_log(log_args)

        # Should produce minimal output
        captured = capsys.readouterr()
        output = captured.out

        assert "digraph veslog{" in output
        assert "node[shape=rect]" in output
        assert "}" in output
        # Should not contain any commit nodes
        assert "c_" not in output

    def test_log_handles_cycles(self, temp_dir, clean_env, capsys):
        """Test that log_graphviz handles seen set correctly to avoid infinite loops."""
        os.chdir(temp_dir)

        # Initialize repository and create a commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Cycle test")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Cycle test commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Call log_graphviz multiple times with same seen set
        seen = set()
        log_graphviz(repo, commit_sha, seen)

        # Clear captured output
        capsys.readouterr()

        # Call again - should not produce output since SHA is in seen
        log_graphviz(repo, commit_sha, seen)

        captured = capsys.readouterr()
        output = captured.out

        # Should be empty since commit was already processed
        assert output.strip() == ""
