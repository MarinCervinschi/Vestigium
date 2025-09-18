import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.cat_file import cmd_cat_file
from src.commands.hash_object import cmd_hash_object
from src.commands.init import cmd_init
from src.core.objects import VesBlob, object_read, object_write
from src.core.repository import repo_find


class TestCatFileCommand:
    """Test cases for the cat-file command."""

    def test_cat_file_basic_functionality(self, temp_dir, clean_env, capsys):
        """Test that cat-file command runs without crashing."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        test_content = b"Hello, World!\nThis is a test file.\n"
        blob = VesBlob(data=test_content)
        obj_hash = object_write(blob, repo)

        # Test cat-file command - should not crash
        args = Namespace(object=obj_hash, type="blob")
        cmd_cat_file(args)

        # Verify the object exists and can be read back
        obj = object_read(repo, obj_hash)
        assert obj is not None
        assert obj.serialize() == test_content

    def test_cat_file_object_not_found(self, temp_dir, clean_env, capsys):
        """Test that cat-file handles non-existent objects gracefully."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        fake_hash = "a" * 40  # Valid format but non-existent
        args = Namespace(object=fake_hash, type="blob")

        with pytest.raises(Exception, match=f"No such reference {fake_hash}."):
            cmd_cat_file(args)

    def test_cat_file_outside_repository(self, temp_dir, clean_env, capsys):
        """Test that cat-file fails gracefully outside a repository."""
        os.chdir(temp_dir)

        fake_hash = "a" * 40
        args = Namespace(object=fake_hash, type="blob")

        with pytest.raises(Exception, match="No ves directory."):
            cmd_cat_file(args)

    def test_cat_file_with_hash_object_integration(self, temp_dir, clean_env, capsys):
        """Test integration between hash-object and cat-file commands."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        test_file = repo_path / "integration_test.txt"
        test_content = b"Integration test content\nSecond line\n"
        test_file.write_bytes(test_content)

        hash_args = Namespace(path=str(test_file), type="blob", write=True)
        cmd_hash_object(hash_args)

        captured = capsys.readouterr()
        obj_hash = captured.out.strip()

        assert len(obj_hash) == 40
        assert all(c in "0123456789abcdef" for c in obj_hash.lower())

        cat_args = Namespace(object=obj_hash, type="blob")
        cmd_cat_file(cat_args)

        repo = repo_find()
        assert repo is not None
        obj = object_read(repo, obj_hash)
        assert obj is not None
        assert obj.serialize() == test_content

    def test_cat_file_empty_blob(self, temp_dir, clean_env):
        """Test cat-file with empty blob content."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        empty_blob = VesBlob(data=b"")
        empty_hash = object_write(empty_blob, repo)

        args = Namespace(object=empty_hash, type="blob")
        cmd_cat_file(args)

        obj = object_read(repo, empty_hash)
        assert obj is not None
        assert obj.serialize() == b""

    def test_cat_file_binary_content(self, temp_dir, clean_env):
        """Test cat-file with binary blob content."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        binary_content = bytes(range(256))  # All possible byte values
        binary_blob = VesBlob(data=binary_content)
        binary_hash = object_write(binary_blob, repo)

        args = Namespace(object=binary_hash, type="blob")
        cmd_cat_file(args)

        obj = object_read(repo, binary_hash)
        assert obj is not None
        assert obj.serialize() == binary_content

    def test_cat_file_large_blob(self, temp_dir, clean_env):
        """Test cat-file with large blob content."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create large blob (smaller size for testing)
        large_content = b"A" * 10000  # 10KB should be enough for testing
        large_blob = VesBlob(data=large_content)
        large_hash = object_write(large_blob, repo)

        args = Namespace(object=large_hash, type="blob")
        cmd_cat_file(args)

        obj = object_read(repo, large_hash)
        assert obj is not None
        assert obj.serialize() == large_content

    def test_cat_file_different_types_accepted(self, temp_dir, clean_env):
        """Test that cat-file accepts different object type parameters."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        test_content = b"test content"
        blob = VesBlob(data=test_content)
        blob_hash = object_write(blob, repo)

        # Test with different type specifications (should all work for blob objects)
        for obj_type in ["blob", "tree", "commit", "tag"]:
            args = Namespace(object=blob_hash, type=obj_type)
            # Should not crash regardless of type specified
            cmd_cat_file(args)
