import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.hash_object import cmd_hash_object
from src.commands.init import cmd_init
from src.core.objects import object_read
from src.core.repository import repo_find


class TestHashObjectCommand:
    """Test cases for the hash-object command."""

    def test_hash_object_without_write(self, temp_dir, clean_env, capsys):
        """Test that hash-object calculates hash without writing to repository."""
        os.chdir(temp_dir)

        test_file = Path(temp_dir) / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        args = Namespace(path=str(test_file), type="blob", write=False)
        cmd_hash_object(args)

        captured = capsys.readouterr()
        hash_output = captured.out.strip()

        assert len(hash_output) == 40
        assert all(c in "0123456789abcdef" for c in hash_output.lower())

        # Verify consistent hashing - same content should produce same hash
        args2 = Namespace(path=str(test_file), type="blob", write=False)
        cmd_hash_object(args2)

        captured2 = capsys.readouterr()
        hash_output2 = captured2.out.strip()

        assert hash_output == hash_output2

    def test_hash_object_with_write(self, temp_dir, clean_env, capsys):
        """Test that hash-object writes object to repository when --write is used."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        test_file = repo_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        args = Namespace(path=str(test_file), type="blob", write=True)
        cmd_hash_object(args)

        captured = capsys.readouterr()
        hash_output = captured.out.strip()

        # Verify the object was written to the repository
        repo = repo_find()
        assert repo is not None

        # Try to read the object back
        obj = object_read(repo, hash_output)
        assert obj is not None
        assert obj.serialize() == test_content

    def test_hash_object_different_types(self, temp_dir, clean_env, capsys):
        """Test that hash-object works with different object types."""
        os.chdir(temp_dir)

        # Test blob type
        blob_file = Path(temp_dir) / "test.txt"
        blob_content = b"Hello, World!"
        blob_file.write_bytes(blob_content)

        blob_args = Namespace(path=str(blob_file), type="blob", write=False)
        cmd_hash_object(blob_args)
        blob_hash = capsys.readouterr().out.strip()

        # Test commit type with proper KVLM format
        commit_file = Path(temp_dir) / "test_commit.txt"
        commit_content = b"tree 3b18e512dba79e4c8300dd08aeb37f8e728b8dad\nauthor Test User <test@example.com> 1234567890 +0000\ncommitter Test User <test@example.com> 1234567890 +0000\n\nTest commit message\n"
        commit_file.write_bytes(commit_content)

        commit_args = Namespace(path=str(commit_file), type="commit", write=False)
        cmd_hash_object(commit_args)
        commit_hash = capsys.readouterr().out.strip()

        # Test tag type with proper KVLM format
        tag_file = Path(temp_dir) / "test_tag.txt"
        tag_content = b"object 3b18e512dba79e4c8300dd08aeb37f8e728b8dad\ntype commit\ntag v1.0\ntagger Test User <test@example.com> 1234567890 +0000\n\nTest tag message\n"
        tag_file.write_bytes(tag_content)

        tag_args = Namespace(path=str(tag_file), type="tag", write=False)
        cmd_hash_object(tag_args)
        tag_hash = capsys.readouterr().out.strip()

        # Different types should produce different hashes
        assert blob_hash != commit_hash
        assert blob_hash != tag_hash
        assert commit_hash != tag_hash

        # Verify all hashes are valid SHA-1 (40 hex characters)
        assert len(blob_hash) == 40
        assert len(commit_hash) == 40
        assert len(tag_hash) == 40
        assert all(c in "0123456789abcdef" for c in blob_hash.lower())
        assert all(c in "0123456789abcdef" for c in commit_hash.lower())
        assert all(c in "0123456789abcdef" for c in tag_hash.lower())

    def test_hash_object_empty_file(self, temp_dir, clean_env, capsys):
        """Test that hash-object handles empty files correctly."""
        os.chdir(temp_dir)

        # Create an empty test file
        test_file = Path(temp_dir) / "empty.txt"
        test_file.write_bytes(b"")

        args = Namespace(path=str(test_file), type="blob", write=False)
        cmd_hash_object(args)

        captured = capsys.readouterr()
        hash_output = captured.out.strip()

        assert len(hash_output) == 40
        assert all(c in "0123456789abcdef" for c in hash_output.lower())

    def test_hash_object_binary_file(self, temp_dir, clean_env, capsys):
        """Test that hash-object handles binary files correctly."""
        os.chdir(temp_dir)

        test_file = Path(temp_dir) / "binary.bin"
        binary_content = bytes(range(256))  # All possible byte values
        test_file.write_bytes(binary_content)

        args = Namespace(path=str(test_file), type="blob", write=False)
        cmd_hash_object(args)

        captured = capsys.readouterr()
        hash_output = captured.out.strip()

        assert len(hash_output) == 40
        assert all(c in "0123456789abcdef" for c in hash_output.lower())

    def test_hash_object_large_file(self, temp_dir, clean_env, capsys):
        """Test that hash-object handles larger files correctly."""
        os.chdir(temp_dir)

        # Create a larger test file (1MB)
        test_file = Path(temp_dir) / "large.txt"
        large_content = b"A" * (1024 * 1024)
        test_file.write_bytes(large_content)

        args = Namespace(path=str(test_file), type="blob", write=False)
        cmd_hash_object(args)

        captured = capsys.readouterr()
        hash_output = captured.out.strip()

        assert len(hash_output) == 40
        assert all(c in "0123456789abcdef" for c in hash_output.lower())

    def test_hash_object_file_not_found(self, temp_dir, clean_env):
        """Test that hash-object fails gracefully when file doesn't exist."""
        os.chdir(temp_dir)

        non_existent_file = Path(temp_dir) / "nonexistent.txt"
        args = Namespace(path=str(non_existent_file), type="blob", write=False)

        with pytest.raises(FileNotFoundError):
            cmd_hash_object(args)

    def test_hash_object_write_without_repository(self, temp_dir, clean_env):
        """Test that hash-object with --write fails outside a repository."""
        os.chdir(temp_dir)

        test_file = Path(temp_dir) / "test.txt"
        test_file.write_bytes(b"test content")

        args = Namespace(path=str(test_file), type="blob", write=True)

        # Should fail because we're not in a repository
        with pytest.raises(Exception):
            cmd_hash_object(args)

    def test_hash_object_consistency_with_git(self, temp_dir, clean_env, capsys):
        """Test that our hash matches expected Ves behavior for known content."""
        os.chdir(temp_dir)

        test_file = Path(temp_dir) / "hello.txt"
        test_content = b"hello world\n"
        test_file.write_bytes(test_content)

        args = Namespace(path=str(test_file), type="blob", write=False)
        cmd_hash_object(args)

        captured = capsys.readouterr()
        hash_output = captured.out.strip()

        # This should match Ves's hash for "hello world\n" as a blob
        # Ves: echo "hello world" | git hash-object --stdin
        # Expected: 3b18e512dba79e4c8300dd08aeb37f8e728b8dad
        expected_hash = "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"
        assert hash_output == expected_hash
