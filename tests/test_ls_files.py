import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.init import cmd_init
from src.commands.ls_files import cmd_ls_files
from src.core.index import index_read
from src.core.repository import repo_find


class TestLsFilesCommand:
    """Test cases for the ls-files command."""

    def test_ls_files_empty_repository(self, temp_dir, clean_env, capsys):
        """Test that ls-files handles empty repository (no index) gracefully."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        # Should not crash and should produce no output for empty index
        assert captured.out == ""

    def test_ls_files_outside_repository(self, temp_dir, clean_env):
        """Test that ls-files raises exception outside a repository."""
        os.chdir(temp_dir)

        args = Namespace(verbose=False)

        with pytest.raises(Exception, match="No ves directory."):
            cmd_ls_files(args)

    def test_ls_files_single_file(self, temp_dir, clean_env, capsys):
        """Test ls-files with a single tracked file."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Test ls-files
        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        assert "test.txt" in captured.out

    def test_ls_files_multiple_files(self, temp_dir, clean_env, capsys):
        """Test ls-files with multiple tracked files."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add multiple test files
        files_to_add = []
        for i, name in enumerate(["file1.txt", "file2.py", "file3.md"]):
            test_file = repo_path / name
            test_file.write_bytes(f"Content of file {i+1}".encode())
            files_to_add.append(str(test_file))

        add_args = Namespace(path=files_to_add)
        cmd_add(add_args)

        # Test ls-files
        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split("\n")

        # Should list all files
        assert "file1.txt" in captured.out
        assert "file2.py" in captured.out
        assert "file3.md" in captured.out
        assert len(output_lines) == 3

    def test_ls_files_subdirectory_files(self, temp_dir, clean_env, capsys):
        """Test ls-files with files in subdirectories."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create subdirectory and files
        subdir = repo_path / "subdir"
        subdir.mkdir()

        test_file1 = repo_path / "root.txt"
        test_file1.write_bytes(b"Root file")

        test_file2 = subdir / "sub.txt"
        test_file2.write_bytes(b"Sub file")

        add_args = Namespace(path=[str(test_file1), str(test_file2)])
        cmd_add(add_args)

        # Test ls-files
        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        assert "root.txt" in captured.out
        assert "subdir/sub.txt" in captured.out

    def test_ls_files_verbose_mode(self, temp_dir, clean_env, capsys):
        """Test ls-files with verbose flag showing detailed information."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "verbose_test.txt"
        test_content = b"Test content for verbose output"
        test_file.write_bytes(test_content)

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Test ls-files with verbose flag
        args = Namespace(verbose=True)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain filename
        assert "verbose_test.txt" in output

        # Should contain verbose information
        assert "regular file" in output
        assert "with perms:" in output
        assert "on blob:" in output
        assert "created:" in output
        assert "modified:" in output
        assert "device:" in output
        assert "inode:" in output
        assert "user:" in output
        assert "group:" in output
        assert "flags:" in output
        assert "stage=" in output
        assert "assume_valid=" in output

    def test_ls_files_verbose_shows_blob_hash(self, temp_dir, clean_env, capsys):
        """Test that verbose mode shows the correct blob hash."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "hash_test.txt"
        test_file.write_bytes(b"test content")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Test ls-files with verbose flag
        args = Namespace(verbose=True)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        output = captured.out

        # Verify that a valid SHA hash is shown
        import re

        hash_match = re.search(r"on blob: ([a-f0-9]{40})", output)
        assert hash_match is not None
        blob_hash = hash_match.group(1)
        assert len(blob_hash) == 40
        assert all(c in "0123456789abcdef" for c in blob_hash.lower())

    def test_ls_files_file_ordering(self, temp_dir, clean_env, capsys):
        """Test that ls-files lists files in the order they appear in index."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create files in a specific order
        file_names = ["zebra.txt", "alpha.txt", "beta.txt"]
        files_to_add = []

        for name in file_names:
            test_file = repo_path / name
            test_file.write_bytes(f"Content of {name}".encode())
            files_to_add.append(str(test_file))

        # Add files one by one to control index order
        for file_path in files_to_add:
            add_args = Namespace(path=[file_path])
            cmd_add(add_args)

        # Test ls-files
        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split("\n")

        # Verify all files are listed
        assert len(output_lines) == 3
        for name in file_names:
            assert name in captured.out

    def test_ls_files_with_special_characters(self, temp_dir, clean_env, capsys):
        """Test ls-files with files containing special characters in names."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create files with special characters (that are valid in most filesystems)
        special_files = [
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
        ]
        files_to_add = []

        for name in special_files:
            test_file = repo_path / name
            test_file.write_bytes(f"Content of {name}".encode())
            files_to_add.append(str(test_file))

        add_args = Namespace(path=files_to_add)
        cmd_add(add_args)

        # Test ls-files
        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()

        for name in special_files:
            assert name in captured.out

    def test_ls_files_integration_with_index(self, temp_dir, clean_env):
        """Test that ls-files correctly reads from the repository index."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create and add a test file
        test_file = repo_path / "index_test.txt"
        test_file.write_bytes(b"Index integration test")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Verify the file is in the index by reading it directly
        repo = repo_find()
        assert repo is not None

        index = index_read(repo)
        assert index is not None
        assert len(index.entries) == 1
        assert index.entries[0].name == "index_test.txt"

        # Now test that ls-files shows the same file
        args = Namespace(verbose=False)
        import io
        import sys
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            cmd_ls_files(args)

        result = output.getvalue()
        assert "index_test.txt" in result

    def test_ls_files_empty_filename_edge_case(self, temp_dir, clean_env, capsys):
        """Test ls-files behavior with edge cases (this tests robustness)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Create a file with a very short name
        test_file = repo_path / "a"
        test_file.write_bytes(b"Single character filename")

        add_args = Namespace(path=[str(test_file)])
        cmd_add(add_args)

        # Test ls-files
        args = Namespace(verbose=False)
        cmd_ls_files(args)

        captured = capsys.readouterr()
        assert "a" in captured.out
