import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.init import cmd_init
from src.commands.rev_parse import cmd_rev_parse
from src.core.objects import VesBlob, object_write
from src.core.refs import ref_create
from src.core.repository import repo_find


class TestRevParseCommand:
    """Test cases for the rev-parse command."""

    def test_rev_parse_outside_repository(self, temp_dir, clean_env):
        """Test that rev-parse raises exception outside a repository."""
        os.chdir(temp_dir)

        args = Namespace(name="HEAD", type=None)

        with pytest.raises(Exception, match="No ves directory."):
            cmd_rev_parse(args)

    def test_rev_parse_head_in_new_repository(self, temp_dir, clean_env, capsys):
        """Test rev-parse with HEAD in a newly initialized repository."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a master branch with a commit SHA
        master_sha = "a" * 40
        ref_create(repo, "heads/master", master_sha)

        # Test rev-parse with HEAD
        args = Namespace(name="HEAD", type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should resolve HEAD to master SHA
        assert output == master_sha

    def test_rev_parse_full_sha(self, temp_dir, clean_env, capsys):
        """Test rev-parse with full SHA hash."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob object
        blob = VesBlob(data=b"test content for rev-parse")
        blob_sha = object_write(blob, repo)

        # Test rev-parse with full SHA
        args = Namespace(name=blob_sha, type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should return the same SHA
        assert output == blob_sha

    def test_rev_parse_partial_sha(self, temp_dir, clean_env, capsys):
        """Test rev-parse with partial SHA hash."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob object
        blob = VesBlob(data=b"unique content for partial sha test")
        blob_sha = object_write(blob, repo)

        # Test rev-parse with partial SHA (first 8 characters)
        partial_sha = blob_sha[:8]
        args = Namespace(name=partial_sha, type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should resolve to full SHA
        assert output == blob_sha

    def test_rev_parse_branch_name(self, temp_dir, clean_env, capsys):
        """Test rev-parse with branch name."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a branch
        develop_sha = "b" * 40
        ref_create(repo, "heads/develop", develop_sha)

        # Test rev-parse with branch name
        args = Namespace(name="develop", type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should resolve to branch SHA
        assert output == develop_sha

    def test_rev_parse_tag_name(self, temp_dir, clean_env, capsys):
        """Test rev-parse with tag name."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a tag
        tag_sha = "c" * 40
        ref_create(repo, "tags/v1.0", tag_sha)

        # Test rev-parse with tag name
        args = Namespace(name="v1.0", type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should resolve to tag SHA
        assert output == tag_sha

    def test_rev_parse_feature_branch(self, temp_dir, clean_env, capsys):
        """Test rev-parse with feature branch name."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a feature branch with simple name
        feature_sha = "d" * 40
        ref_create(repo, "heads/feature", feature_sha)

        # Test rev-parse with feature branch name
        args = Namespace(name="feature", type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should resolve to feature branch SHA
        assert output == feature_sha

    def test_rev_parse_with_type_filter(self, temp_dir, clean_env, capsys):
        """Test rev-parse with type filtering."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob object
        blob = VesBlob(data=b"test content for type filtering")
        blob_sha = object_write(blob, repo)

        # Test rev-parse with blob type filter
        args = Namespace(name=blob_sha, type="blob")
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should return the blob SHA since it matches the type
        assert output == blob_sha

    def test_rev_parse_nonexistent_reference(self, temp_dir, clean_env):
        """Test rev-parse with non-existent reference."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Test rev-parse with non-existent reference
        args = Namespace(name="nonexistent-branch", type=None)

        with pytest.raises(Exception, match="No such reference nonexistent-branch"):
            cmd_rev_parse(args)

    def test_rev_parse_nonexistent_sha(self, temp_dir, clean_env):
        """Test rev-parse with non-existent SHA."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Test rev-parse with non-existent SHA
        fake_sha = "f" * 40
        args = Namespace(name=fake_sha, type=None)

        with pytest.raises(Exception, match=f"No such reference {fake_sha}"):
            cmd_rev_parse(args)

    def test_rev_parse_ambiguous_reference(self, temp_dir, clean_env):
        """Test rev-parse with ambiguous partial SHA."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create multiple blobs with similar SHA prefixes
        # This is tricky to test reliably since we can't control the exact SHA
        # So we'll create objects and see if any create ambiguity

        blob1 = VesBlob(data=b"content1")
        sha1 = object_write(blob1, repo)

        blob2 = VesBlob(data=b"content2")
        sha2 = object_write(blob2, repo)

        # If the first 4 characters are the same, it would be ambiguous
        if sha1[:4] == sha2[:4]:
            args = Namespace(name=sha1[:4], type=None)
            with pytest.raises(Exception, match="Ambiguous reference"):
                cmd_rev_parse(args)
        else:
            # If not ambiguous, test should pass
            args = Namespace(name=sha1[:4], type=None)
            cmd_rev_parse(args)

    def test_rev_parse_empty_name(self, temp_dir, clean_env):
        """Test rev-parse with empty or whitespace name."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Test rev-parse with empty name
        args = Namespace(name="", type=None)

        with pytest.raises(Exception, match="No such reference"):
            cmd_rev_parse(args)

        # Test rev-parse with whitespace name
        args = Namespace(name="   ", type=None)

        with pytest.raises(Exception, match="No such reference"):
            cmd_rev_parse(args)

    def test_rev_parse_case_insensitive_sha(self, temp_dir, clean_env, capsys):
        """Test that rev-parse handles SHA hashes case-insensitively."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob object
        blob = VesBlob(data=b"case sensitivity test")
        blob_sha = object_write(blob, repo)

        # Test with uppercase partial SHA
        upper_partial = blob_sha[:8].upper()
        args = Namespace(name=upper_partial, type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Should resolve to full SHA regardless of case
        assert output == blob_sha

    def test_rev_parse_minimum_sha_length(self, temp_dir, clean_env):
        """Test rev-parse with minimum SHA length (4 characters)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a blob object
        blob = VesBlob(data=b"minimum length test")
        blob_sha = object_write(blob, repo)

        # Test with 4-character SHA (minimum)
        args = Namespace(name=blob_sha[:4], type=None)
        cmd_rev_parse(args)

        # Should not raise exception with 4 characters

    def test_rev_parse_invalid_sha_format(self, temp_dir, clean_env):
        """Test rev-parse with invalid SHA format."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Test with invalid characters in SHA
        args = Namespace(name="invalid-sha-format", type=None)

        with pytest.raises(Exception, match="No such reference"):
            cmd_rev_parse(args)

    def test_rev_parse_too_short_sha(self, temp_dir, clean_env):
        """Test rev-parse with too short SHA (less than 4 characters)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Test with 3-character string (too short for SHA)
        args = Namespace(name="abc", type=None)

        with pytest.raises(Exception, match="No such reference"):
            cmd_rev_parse(args)

    def test_rev_parse_priority_order(self, temp_dir, clean_env, capsys):
        """Test that rev-parse follows correct priority order for name resolution."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a tag and branch with the same name
        tag_sha = "1" * 40
        branch_sha = "2" * 40

        ref_create(repo, "tags/test", tag_sha)
        ref_create(repo, "heads/test", branch_sha)

        # Test rev-parse with the ambiguous name
        args = Namespace(name="test", type=None)

        # Should raise exception for ambiguous reference
        with pytest.raises(Exception, match="Ambiguous reference test"):
            cmd_rev_parse(args)

    def test_rev_parse_none_type_argument(self, temp_dir, clean_env, capsys):
        """Test rev-parse with None type argument (default case)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a test reference
        test_sha = "3" * 40
        ref_create(repo, "heads/type-test", test_sha)

        # Test with None type (should not filter by type)
        args = Namespace(name="type-test", type=None)
        cmd_rev_parse(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert output == test_sha
