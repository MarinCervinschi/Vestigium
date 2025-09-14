import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.init import cmd_init
from src.commands.show_ref import cmd_show_ref, show_ref
from src.core.refs import ref_create, ref_list, ref_resolve
from src.core.repository import repo_find


class TestShowRefCommand:
    """Test cases for the show-ref command."""

    def test_show_ref_outside_repository(self, temp_dir, clean_env):
        """Test that show-ref raises exception outside a repository."""
        os.chdir(temp_dir)

        args = Namespace()

        with pytest.raises(Exception, match="No ves directory."):
            cmd_show_ref(args)

    def test_show_ref_empty_repository(self, temp_dir, clean_env, capsys):
        """Test show-ref in a new repository with only default refs."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # New repository might have no refs or only have basic structure
        # Should not crash and output should be well-formed
        if output:
            lines = output.strip().split("\n")
            for line in lines:
                # Each line should have format: "{sha} refs/{path}"
                parts = line.split(" ", 1)
                assert len(parts) == 2
                sha, ref_path = parts
                assert len(sha) == 40  # Valid SHA
                assert ref_path.startswith("refs/")

    def test_show_ref_with_created_branch(self, temp_dir, clean_env, capsys):
        """Test show-ref with manually created branch reference."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a fake branch reference
        fake_sha = "a" * 40
        ref_create(repo, "heads/master", fake_sha)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show the created branch
        assert fake_sha in output
        assert "refs/heads/master" in output

    def test_show_ref_with_multiple_refs(self, temp_dir, clean_env, capsys):
        """Test show-ref with multiple references (branches and tags)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create multiple references
        master_sha = "a" * 40
        develop_sha = "b" * 40
        tag_sha = "c" * 40

        ref_create(repo, "heads/master", master_sha)
        ref_create(repo, "heads/develop", develop_sha)
        ref_create(repo, "tags/v1.0", tag_sha)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show all references
        assert master_sha in output
        assert develop_sha in output
        assert tag_sha in output
        assert "refs/heads/master" in output
        assert "refs/heads/develop" in output
        assert "refs/tags/v1.0" in output

    def test_show_ref_with_multiple_branches_and_tags(
        self, temp_dir, clean_env, capsys
    ):
        """Test show-ref with multiple local branches and tags."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create multiple local references (branches and tags) - using simple names
        master_sha = "a" * 40
        develop_sha = "b" * 40
        feature_sha = "c" * 40
        tag_sha = "d" * 40

        ref_create(repo, "heads/master", master_sha)
        ref_create(repo, "heads/develop", develop_sha)
        ref_create(repo, "heads/feature", feature_sha)  # Simplified from nested path
        ref_create(repo, "tags/v1.0", tag_sha)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show all local references
        assert master_sha in output
        assert develop_sha in output
        assert feature_sha in output
        assert tag_sha in output
        assert "refs/heads/master" in output
        assert "refs/heads/develop" in output
        assert "refs/heads/feature" in output  # Updated assertion
        assert "refs/tags/v1.0" in output

    def test_show_ref_with_deeply_nested_branches(self, temp_dir, clean_env, capsys):
        """Test show-ref with branch structure that would require nested directories."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Test with a branch name that looks nested but is treated as a single name
        # This tests the system's handling of branch names with slashes
        nested_sha = "f" * 40

        # Create the nested directory structure manually first
        nested_dir = repo_path / ".ves" / "refs" / "heads" / "feature" / "user-auth"
        nested_dir.mkdir(parents=True, exist_ok=True)

        # Then create the ref file
        ref_file = nested_dir / "login-system"
        ref_file.write_text(nested_sha + "\n")

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show nested reference
        assert nested_sha in output
        assert "refs/heads/feature/user-auth/login-system" in output

    def test_show_ref_function_without_hash(self, temp_dir, clean_env, capsys):
        """Test show_ref function with with_hash=False."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a reference
        test_sha = "1" * 40
        ref_create(repo, "heads/test", test_sha)

        # Get refs and test show_ref function without hash
        refs = ref_list(repo)
        show_ref(repo, refs, with_hash=False, prefix="refs")

        captured = capsys.readouterr()
        output = captured.out

        # Should show reference without SHA
        assert "refs/heads/test" in output
        assert test_sha not in output

    def test_show_ref_function_with_custom_prefix(self, temp_dir, clean_env, capsys):
        """Test show_ref function with custom prefix."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a reference
        test_sha = "2" * 40
        ref_create(repo, "heads/custom", test_sha)

        # Get refs and test show_ref function with custom prefix
        refs = ref_list(repo)
        show_ref(repo, refs, with_hash=True, prefix="custom_prefix")

        captured = capsys.readouterr()
        output = captured.out

        # Should show reference with custom prefix
        assert test_sha in output
        assert "custom_prefix/heads/custom" in output

    def test_show_ref_sorted_output(self, temp_dir, clean_env, capsys):
        """Test that show-ref output is sorted."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create references in non-alphabetical order
        ref_create(repo, "heads/zebra", "z" * 40)
        ref_create(repo, "heads/alpha", "a" * 40)
        ref_create(repo, "heads/beta", "b" * 40)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out
        lines = output.strip().split("\n")

        # Extract just the reference names for sorting check
        ref_names = []
        for line in lines:
            if line:
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    ref_names.append(parts[1])

        # Should be sorted alphabetically
        assert ref_names == sorted(ref_names)

    def test_show_ref_with_symbolic_refs(self, temp_dir, clean_env, capsys):
        """Test show-ref with symbolic references (like HEAD)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a branch and make HEAD point to it
        master_sha = "3" * 40
        ref_create(repo, "heads/master", master_sha)

        # HEAD should already point to refs/heads/master from init
        # Verify symbolic ref resolution works
        head_sha = ref_resolve(repo, "HEAD")
        assert head_sha == master_sha

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show the actual branch, not HEAD (since show-ref shows refs/ directory)
        assert master_sha in output
        assert "refs/heads/master" in output

    def test_show_ref_with_empty_refs_directory(self, temp_dir, clean_env, capsys):
        """Test show-ref with completely empty refs directory."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)

        # Remove all files from refs directory
        refs_dir = repo_path / ".ves" / "refs"
        if refs_dir.exists():
            import shutil

            for item in refs_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should handle empty refs gracefully
        assert output == "" or output.isspace()

    def test_show_ref_unresolvable_refs(self, temp_dir, clean_env, capsys):
        """Test show-ref with references that cannot be resolved."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a symbolic reference pointing to non-existent ref
        broken_ref_file = repo_path / ".ves" / "refs" / "heads" / "broken"
        broken_ref_file.parent.mkdir(parents=True, exist_ok=True)
        broken_ref_file.write_text("ref: refs/heads/nonexistent\n")

        # Create a valid reference for comparison
        ref_create(repo, "heads/valid", "4" * 40)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show valid ref but skip broken one
        assert "refs/heads/valid" in output
        assert "4" * 40 in output
        # Broken ref should not appear (None values are skipped)
        assert "refs/heads/broken" not in output

    def test_show_ref_mixed_ref_types(self, temp_dir, clean_env, capsys):
        """Test show-ref with mixed reference types (direct and symbolic)."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create direct reference
        direct_sha = "5" * 40
        ref_create(repo, "heads/direct", direct_sha)

        # Create symbolic reference pointing to the direct one
        symbolic_ref_file = repo_path / ".ves" / "refs" / "heads" / "symbolic"
        symbolic_ref_file.write_text("ref: refs/heads/direct\n")

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out

        # Both references should show with the same SHA (resolved)
        assert "refs/heads/direct" in output
        assert "refs/heads/symbolic" in output
        # Both should show the same SHA since symbolic points to direct
        assert output.count(direct_sha) == 2

    def test_show_ref_output_format(self, temp_dir, clean_env, capsys):
        """Test that show-ref output has correct format."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)

        os.chdir(repo_path)
        repo = repo_find()
        assert repo is not None

        # Create a test reference
        test_sha = "6" * 40
        ref_create(repo, "heads/format-test", test_sha)

        # Test show-ref command
        args = Namespace()
        cmd_show_ref(args)

        captured = capsys.readouterr()
        output = captured.out.strip()

        if output:
            lines = output.split("\n")
            for line in lines:
                # Each line should match format: "{40-char-sha} refs/{path}"
                parts = line.split(" ", 1)
                assert len(parts) == 2
                sha, ref_path = parts

                # Validate SHA format
                assert len(sha) == 40
                assert all(c in "0123456789abcdef" for c in sha.lower())

                # Validate ref path format
                assert ref_path.startswith("refs/")
                assert (
                    "/" in ref_path[5:]
                )  # Should have at least refs/{category}/{name}
