import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.commit import cmd_commit
from src.commands.init import cmd_init
from src.commands.tag import cmd_tag, tag_create
from src.core.objects import VesTag, object_read
from src.core.refs import ref_list, ref_resolve
from src.core.repository import repo_find


class TestTagCommand:
    """Test cases for the tag command."""

    def test_list_tags_empty_repository(self, temp_dir, clean_env, capsys):
        """Test listing tags in a repository with no tags."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # List tags (should be empty)
        args = Namespace(name=None, object=None, create_tag_object=False)
        cmd_tag(args)

        # Should produce no output for empty tag list
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    def test_create_lightweight_tag(self, temp_dir, clean_env):
        """Test creating a lightweight tag."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Create a lightweight tag
        args = Namespace(name="v1.0", object=commit_sha, create_tag_object=False)
        cmd_tag(args)

        # Verify the tag was created
        refs = ref_list(repo)
        assert "tags" in refs
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        assert "v1.0" in tags_dict
        assert tags_dict["v1.0"] == commit_sha

    def test_create_annotated_tag(self, temp_dir, clean_env):
        """Test creating an annotated tag."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Get the commit SHA
        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Create an annotated tag
        args = Namespace(name="v2.0", object=commit_sha, create_tag_object=True)
        cmd_tag(args)

        # Verify the tag was created
        refs = ref_list(repo)
        assert "tags" in refs
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        assert "v2.0" in tags_dict

        # The tag reference should point to a tag object, not directly to the commit
        tag_sha = tags_dict["v2.0"]
        assert isinstance(tag_sha, str)
        assert tag_sha != commit_sha

        # Read the tag object and verify its content
        tag_obj = object_read(repo, tag_sha)
        assert isinstance(tag_obj, VesTag)
        assert tag_obj.kvlm[b"object"].decode() == commit_sha
        assert tag_obj.kvlm[b"type"] == b"commit"
        assert tag_obj.kvlm[b"tag"] == b"v2.0"
        assert tag_obj.kvlm[b"tagger"] == b"Ves <ves@example.com>"

    def test_list_tags_with_tags(self, temp_dir, clean_env, capsys):
        """Test listing tags when tags exist."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Create multiple tags
        tag1_args = Namespace(name="v1.0", object=commit_sha, create_tag_object=False)
        cmd_tag(tag1_args)

        tag2_args = Namespace(
            name="release", object=commit_sha, create_tag_object=False
        )
        cmd_tag(tag2_args)

        # List tags
        list_args = Namespace(name=None, object=None, create_tag_object=False)
        cmd_tag(list_args)

        # Check output contains both tags
        captured = capsys.readouterr()
        output_lines = captured.out.strip().split("\n")
        tag_names = [line.strip() for line in output_lines if line.strip()]

        assert "v1.0" in tag_names
        assert "release" in tag_names

    def test_create_tag_with_head_reference(self, temp_dir, clean_env):
        """Test creating a tag using HEAD as reference."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Create tag pointing to HEAD
        args = Namespace(name="latest", object="HEAD", create_tag_object=False)
        cmd_tag(args)

        # Verify the tag was created and points to the same commit as HEAD
        repo = repo_find()
        assert repo is not None
        head_sha = ref_resolve(repo, "HEAD")
        refs = ref_list(repo)
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        assert tags_dict["latest"] == head_sha

    def test_create_multiple_tags_same_commit(self, temp_dir, clean_env):
        """Test creating multiple tags pointing to the same commit."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Create multiple tags pointing to the same commit
        tag1_args = Namespace(name="v1.0", object=commit_sha, create_tag_object=False)
        cmd_tag(tag1_args)

        tag2_args = Namespace(name="stable", object=commit_sha, create_tag_object=False)
        cmd_tag(tag2_args)

        # Verify both tags point to the same commit
        refs = ref_list(repo)
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        assert tags_dict["v1.0"] == commit_sha
        assert tags_dict["stable"] == commit_sha

    def test_tag_create_function_direct(self, temp_dir, clean_env):
        """Test calling tag_create function directly."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Call tag_create directly
        tag_create(repo, "direct-tag", commit_sha, create_tag_object=False)

        # Verify the tag was created
        refs = ref_list(repo)
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        assert "direct-tag" in tags_dict
        assert tags_dict["direct-tag"] == commit_sha

    def test_create_tag_invalid_object(self, temp_dir, clean_env):
        """Test creating a tag with invalid object reference fails."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Try to create tag with invalid object
        args = Namespace(name="invalid", object="nonexistent", create_tag_object=False)

        with pytest.raises(Exception, match="No such reference"):
            cmd_tag(args)

    def test_tag_without_repository(self, temp_dir, clean_env):
        """Test that tag command fails when not in a repository."""
        os.chdir(temp_dir)

        # Try to create tag without repository
        args = Namespace(name="test", object="HEAD", create_tag_object=False)

        with pytest.raises(Exception, match="No ves directory."):
            cmd_tag(args)

    def test_create_tag_with_special_characters(self, temp_dir, clean_env):
        """Test creating tags with special characters in names."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Create tags with various name formats
        tag_names = ["v1.0.0", "release-2023", "feature_branch", "v2.0-beta1"]

        for tag_name in tag_names:
            args = Namespace(name=tag_name, object=commit_sha, create_tag_object=False)
            cmd_tag(args)

        # Verify all tags were created
        refs = ref_list(repo)
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        for tag_name in tag_names:
            assert tag_name in tags_dict
            assert tags_dict[tag_name] == commit_sha

    def test_annotated_tag_content(self, temp_dir, clean_env):
        """Test that annotated tag contains expected metadata."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        commit_sha = ref_resolve(repo, "HEAD")
        assert commit_sha is not None

        # Create annotated tag
        tag_create(repo, "annotated-test", commit_sha, create_tag_object=True)

        # Read and verify tag object content
        refs = ref_list(repo)
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        tag_sha = tags_dict["annotated-test"]
        assert isinstance(tag_sha, str)
        tag_obj = object_read(repo, tag_sha)

        assert isinstance(tag_obj, VesTag)
        assert tag_obj.kvlm[b"object"].decode() == commit_sha
        assert tag_obj.kvlm[b"type"] == b"commit"
        assert tag_obj.kvlm[b"tag"] == b"annotated-test"
        assert tag_obj.kvlm[b"tagger"] == b"Ves <ves@example.com>"
        assert b"A tag generated by Ves" in tag_obj.kvlm[None]

    def test_tag_overwrite_existing(self, temp_dir, clean_env):
        """Test that creating a tag with existing name overwrites it."""
        os.chdir(temp_dir)

        # Initialize repository and create initial commit
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        repo = repo_find()
        assert repo is not None
        first_commit_sha = ref_resolve(repo, "HEAD")
        assert first_commit_sha is not None

        # Create first tag
        args = Namespace(
            name="movable", object=first_commit_sha, create_tag_object=False
        )
        cmd_tag(args)

        # Create another commit
        test_file.write_text("Updated content")
        cmd_add(add_args)

        commit_args2 = Namespace(message="Second commit")
        cmd_commit(commit_args2)

        second_commit_sha = ref_resolve(repo, "HEAD")
        assert second_commit_sha is not None

        # Create tag with same name pointing to new commit
        args2 = Namespace(
            name="movable", object=second_commit_sha, create_tag_object=False
        )
        cmd_tag(args2)

        # Verify tag now points to the second commit
        refs = ref_list(repo)
        tags_dict = refs["tags"]
        assert isinstance(tags_dict, dict)
        assert tags_dict["movable"] == second_commit_sha
        assert tags_dict["movable"] != first_commit_sha
