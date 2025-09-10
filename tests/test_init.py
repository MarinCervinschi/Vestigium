import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.init import cmd_init
from src.core.repository import VesRepository, repo_create


class TestInitCommand:
    """Test cases for the init command."""

    def test_init_creates_repository_structure(self, temp_dir, clean_env):
        """Test that init command creates proper repository structure."""
        os.chdir(temp_dir)

        args = Namespace(path="test_repo")

        cmd_init(args)

        repo_path = Path(temp_dir) / "test_repo"
        ves_dir = repo_path / ".ves"

        assert repo_path.exists()
        assert ves_dir.exists()
        assert (ves_dir / "branches").exists()
        assert (ves_dir / "objects").exists()
        assert (ves_dir / "refs" / "tags").exists()
        assert (ves_dir / "refs" / "heads").exists()
        assert (ves_dir / "description").exists()
        assert (ves_dir / "HEAD").exists()
        assert (ves_dir / "config").exists()

    def test_init_creates_default_files(self, temp_dir, clean_env):
        """Test that init command creates default files with correct content."""
        os.chdir(temp_dir)

        args = Namespace(path="test_repo")
        cmd_init(args)

        repo_path = Path(temp_dir) / "test_repo"
        ves_dir = repo_path / ".ves"

        head_content = (ves_dir / "HEAD").read_text()
        assert head_content == "ref: refs/heads/master\n"

        desc_content = (ves_dir / "description").read_text()
        assert "Unnamed repository" in desc_content

        config_file = ves_dir / "config"
        assert config_file.exists()
        assert config_file.stat().st_size > 0

    def test_init_current_directory(self, temp_dir, clean_env):
        """Test that init command works with current directory (default path)."""
        test_dir = Path(temp_dir) / "current_test"
        test_dir.mkdir()
        os.chdir(test_dir)

        args = Namespace(path=".")
        cmd_init(args)

        ves_dir = test_dir / ".ves"
        assert ves_dir.exists()
        assert (ves_dir / "objects").exists()

    def test_init_fails_on_non_empty_ves_directory(self, temp_dir, clean_env):
        """Test that init fails when .ves directory already exists and is not empty."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "existing_repo"
        repo_path.mkdir()
        ves_dir = repo_path / ".ves"
        ves_dir.mkdir()
        (ves_dir / "somefile").touch()  # Make it non-empty

        args = Namespace(path="existing_repo")

        with pytest.raises(Exception, match="not empty"):
            cmd_init(args)

    def test_repository_object_creation(self, temp_dir, clean_env):
        """Test that VesRepository object is created correctly."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        repo = repo_create(str(repo_path))

        assert isinstance(repo, VesRepository)
        assert repo.worktree == str(repo_path)
        assert repo.vesdir == str(repo_path / ".ves")
        assert repo.conf is not None
