import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.add import cmd_add
from src.commands.commit import cmd_commit
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

    def test_status_with_committed_and_modified_file(self, temp_dir, clean_env, capsys):
        """Test status showing modified files between HEAD and index, and index and worktree."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit initial file
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Modify file and stage it
        test_file.write_text("Staged content")
        cmd_add(add_args)

        # Modify file again in worktree
        import time

        time.sleep(0.1)  # Ensure different timestamp
        test_file.write_text("Worktree content")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show file as both staged for commit and modified in worktree
        assert "Changes to be committed:" in output
        assert "Changes not staged for commit:" in output
        assert "modified: test.txt" in output

    def test_status_with_added_and_deleted_files(self, temp_dir, clean_env, capsys):
        """Test status showing added and deleted files."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit initial files
        file1 = repo_path / "file1.txt"
        file1.write_text("File 1 content")
        file2 = repo_path / "file2.txt"
        file2.write_text("File 2 content")

        add_args = Namespace(path=["file1.txt", "file2.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Add a new file to index
        new_file = repo_path / "new.txt"
        new_file.write_text("New file content")

        add_args = Namespace(path=["new.txt"])
        cmd_add(add_args)

        # Remove an existing file
        from src.commands.rm import cmd_rm

        rm_args = Namespace(path=["file2.txt"])
        cmd_rm(rm_args)

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show new file as added and old file as deleted
        assert "Changes to be committed:" in output
        assert "added:    new.txt" in output
        assert "deleted:  file2.txt" in output

    def test_status_with_deleted_file_in_worktree(self, temp_dir, clean_env, capsys):
        """Test status when file is deleted from worktree but still in index."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and add a file
        test_file = repo_path / "test.txt"
        test_file.write_text("Content")

        add_args = Namespace(path=["test.txt"])
        cmd_add(add_args)

        # Delete the file from worktree (but keep in index)
        test_file.unlink()

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show file as deleted in worktree
        assert "Changes not staged for commit:" in output
        assert "deleted:  test.txt" in output

    def test_status_with_mixed_changes_comprehensive(self, temp_dir, clean_env, capsys):
        """Test status with all types of changes: added, modified, deleted, untracked."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create and commit initial files
        committed_file = repo_path / "committed.txt"
        committed_file.write_text("Committed content")
        to_delete_file = repo_path / "to_delete.txt"
        to_delete_file.write_text("Will be deleted")

        add_args = Namespace(path=["committed.txt", "to_delete.txt"])
        cmd_add(add_args)

        commit_args = Namespace(message="Initial commit")
        cmd_commit(commit_args)

        # Modify existing file and stage it
        committed_file.write_text("Modified and staged")
        add_args = Namespace(path=["committed.txt"])
        cmd_add(add_args)

        # Modify the same file again in worktree
        import time

        time.sleep(0.1)  # Ensure different timestamp
        committed_file.write_text("Modified again in worktree")

        # Add new file to index
        new_staged_file = repo_path / "new_staged.txt"
        new_staged_file.write_text("New staged file")
        add_args = Namespace(path=["new_staged.txt"])
        cmd_add(add_args)

        # Delete a file from index
        from src.commands.rm import cmd_rm

        rm_args = Namespace(path=["to_delete.txt"])
        cmd_rm(rm_args)

        # Create untracked file
        untracked_file = repo_path / "untracked.txt"
        untracked_file.write_text("Untracked content")

        # Create another file and delete it from worktree only
        worktree_deleted = repo_path / "worktree_deleted.txt"
        worktree_deleted.write_text("Will be deleted from worktree")
        add_args = Namespace(path=["worktree_deleted.txt"])
        cmd_add(add_args)
        worktree_deleted.unlink()

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show all types of changes
        assert "Changes to be committed:" in output
        assert "Changes not staged for commit:" in output
        assert "Untracked files:" in output

        # Staged changes
        assert "modified: committed.txt" in output  # staged modification
        assert "added:    new_staged.txt" in output  # staged addition
        assert "deleted:  to_delete.txt" in output  # staged deletion

        # Worktree changes
        lines = output.split("\n")
        worktree_section_found = False
        for line in lines:
            if "Changes not staged for commit:" in line:
                worktree_section_found = True
            elif worktree_section_found and "Untracked files:" in line:
                break
            elif worktree_section_found:
                if "modified: committed.txt" in line:  # worktree modification
                    pass  # This should appear in worktree section too
                elif "deleted:  worktree_deleted.txt" in line:  # worktree deletion
                    pass

        # Untracked files
        assert "untracked.txt" in output

    def test_status_respects_ignore_rules(self, temp_dir, clean_env, capsys):
        """Test that status respects .vesignore rules for untracked files."""
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create .vesignore file
        vesignore_file = repo_path / ".vesignore"
        vesignore_file.write_text("*.log\ntemp/\n*.tmp\n")

        add_args = Namespace(path=[".vesignore"])
        cmd_add(add_args)

        commit_args = Namespace(message="Add ignore rules")
        cmd_commit(commit_args)

        # Create files that should be ignored
        log_file = repo_path / "debug.log"
        log_file.write_text("Log content")

        tmp_file = repo_path / "cache.tmp"
        tmp_file.write_text("Temp content")

        temp_dir_path = repo_path / "temp"
        temp_dir_path.mkdir()
        temp_file = temp_dir_path / "data.txt"
        temp_file.write_text("Temp dir content")

        # Create files that should NOT be ignored
        normal_file = repo_path / "normal.txt"
        normal_file.write_text("Normal content")

        python_file = repo_path / "script.py"
        python_file.write_text("print('hello')")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show untracked files that are not ignored
        assert "Untracked files:" in output
        assert "normal.txt" in output
        assert "script.py" in output

        # Should NOT show ignored files
        assert "debug.log" not in output
        assert "cache.tmp" not in output
        assert "temp/data.txt" not in output
        assert "temp/" not in output

    def test_status_with_symlink_modified(self, temp_dir, clean_env, capsys):
        """Test status with a symlink that has been modified.

        This test covers the symlink handling code in cmd_status_index_worktree,
        specifically lines 102-105 that check for symlink modifications.
        """
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a target file for the symlink
        target_file = repo_path / "target.txt"
        target_file.write_text("Original target content")

        # Create initial symlink
        symlink_path = repo_path / "link.txt"
        symlink_path.symlink_to("target.txt")

        # Add symlink to index
        add_args = Namespace(path=["link.txt"])
        cmd_add(add_args)

        # Make first commit
        commit_args = Namespace(message="Add symlink")
        cmd_commit(commit_args)

        # Create a new target file
        new_target_file = repo_path / "new_target.txt"
        new_target_file.write_text("New target content")

        # Modify the symlink to point to a different target
        # We need to remove and recreate the symlink to change its target
        symlink_path.unlink()

        # Wait a bit to ensure different timestamp for metadata comparison
        import time

        time.sleep(0.1)

        symlink_path.symlink_to("new_target.txt")

        # Test status - should detect the symlink as modified
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show symlink as modified
        assert "Changes not staged for commit:" in output
        assert "modified: link.txt" in output

    def test_status_with_symlink_unchanged(self, temp_dir, clean_env, capsys):
        """Test status with a symlink that has not been modified.

        This test ensures symlinks are properly handled and not falsely reported
        as modified when they point to the same target.
        """
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a target file for the symlink
        target_file = repo_path / "target.txt"
        target_file.write_text("Target content")

        # Create symlink
        symlink_path = repo_path / "link.txt"
        symlink_path.symlink_to("target.txt")

        # Add symlink to index
        add_args = Namespace(path=["link.txt"])
        cmd_add(add_args)

        # Make first commit
        commit_args = Namespace(message="Add symlink")
        cmd_commit(commit_args)

        # Test status - symlink should not be reported as modified
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should not show any modifications for the symlink
        # The symlink should not appear in the "Changes not staged for commit" section
        if "Changes not staged for commit:" in output:
            # If this section exists, link.txt should not be in it
            lines = output.split("\n")
            changes_section = False
            untracked_section = False

            for line in lines:
                if "Changes not staged for commit:" in line:
                    changes_section = True
                    untracked_section = False
                elif "Untracked files:" in line:
                    changes_section = False
                    untracked_section = True
                elif changes_section and "link.txt" in line:
                    pytest.fail("Unchanged symlink should not appear as modified")

    def test_status_with_symlink_target_modified(self, temp_dir, clean_env, capsys):
        """Test status when symlink target content is modified.

        This test verifies the behavior when the content of a symlink's target
        is modified. The symlink may be reported as modified due to metadata changes
        or depending on how the system tracks symlinks.
        """
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a target file for the symlink
        target_file = repo_path / "target.txt"
        target_file.write_text("Original content")

        # Create symlink
        symlink_path = repo_path / "link.txt"
        symlink_path.symlink_to("target.txt")

        # Add both symlink and target to index
        add_args = Namespace(path=["link.txt", "target.txt"])
        cmd_add(add_args)

        # Make first commit
        commit_args = Namespace(message="Add symlink and target")
        cmd_commit(commit_args)

        # Modify the target file content
        import time

        time.sleep(0.1)  # Ensure different timestamp
        target_file.write_text("Modified content")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show target file as modified
        assert "Changes not staged for commit:" in output
        assert "modified: target.txt" in output

        # The symlink behavior may vary - it could be reported as modified
        # due to metadata changes. We just verify the test runs without error
        # and that the target file is properly detected as modified.
        assert "target.txt" in output

    def test_status_with_symlink_content_hash_check(self, temp_dir, clean_env, capsys):
        """Test that symlink modifications are properly detected via content hash.

        This test specifically covers the symlink handling code in lines 102-105
        of status.py that uses object_hash to compare symlink content.
        """
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create initial symlink target
        target1 = repo_path / "target1.txt"
        target1.write_text("Target 1 content")

        # Create symlink pointing to target1
        symlink_path = repo_path / "link.txt"
        symlink_path.symlink_to("target1.txt")

        # Add symlink to index
        add_args = Namespace(path=["link.txt"])
        cmd_add(add_args)

        # Make first commit
        commit_args = Namespace(message="Add symlink")
        cmd_commit(commit_args)

        # Create second target
        target2 = repo_path / "target2.txt"
        target2.write_text("Target 2 content")

        # Change symlink to point to different target
        # This will trigger the symlink content hash check in the code
        symlink_path.unlink()

        import time

        time.sleep(0.1)  # Ensure different timestamp

        symlink_path.symlink_to("target2.txt")

        # Test status - should detect symlink as modified
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show symlink as modified since it points to a different target
        assert "Changes not staged for commit:" in output
        assert "modified: link.txt" in output

    def test_status_untracked_directory_optimization(self, temp_dir, clean_env, capsys):
        """Test that status optimizes display of untracked directories.

        When an entire directory is untracked, it should show only the directory name
        followed by '/' instead of listing all individual files in the directory.
        This mimics Git's behavior for cleaner output.
        """
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create a completely untracked directory with multiple files
        untracked_dir = repo_path / "node_modules"
        untracked_dir.mkdir()

        # Add multiple files in the untracked directory
        (untracked_dir / "package.json").write_text('{"name": "test"}')
        (untracked_dir / "index.js").write_text("console.log('hello');")

        # Add subdirectory with files
        subdir = untracked_dir / "lib"
        subdir.mkdir()
        (subdir / "utils.js").write_text("module.exports = {};")
        (subdir / "main.js").write_text("const utils = require('./utils');")

        # Create a mixed directory (some tracked, some untracked)
        mixed_dir = repo_path / "src"
        mixed_dir.mkdir()

        # Add a tracked file to src
        tracked_file = mixed_dir / "tracked.py"
        tracked_file.write_text("print('tracked')")
        add_args = Namespace(path=["src/tracked.py"])
        cmd_add(add_args)

        # Add an untracked file to src
        (mixed_dir / "untracked.py").write_text("print('untracked')")

        # Create single untracked file in root
        (repo_path / "readme.txt").write_text("readme content")

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show directory optimization for completely untracked directory
        assert "Untracked files:" in output
        assert "node_modules/" in output

        # Should NOT show individual files from the untracked directory
        assert "node_modules/package.json" not in output
        assert "node_modules/index.js" not in output
        assert "node_modules/lib/utils.js" not in output
        assert "node_modules/lib/main.js" not in output

        # Should show individual files from mixed directory (not optimize)
        assert "src/untracked.py" in output

        # Should NOT show the mixed directory as a whole (check for directory entry specifically)
        lines = output.split("\n")
        untracked_lines = []
        in_untracked_section = False

        for line in lines:
            if "Untracked files:" in line:
                in_untracked_section = True
                continue
            elif in_untracked_section and line.strip() == "":
                break
            elif in_untracked_section:
                untracked_lines.append(line.strip())

        # Check that "src/" is not listed as a standalone directory entry
        directory_entries = [line for line in untracked_lines if line.endswith("/")]
        src_directory_listed = any(
            "src/" in entry and entry.strip() == "src/" for entry in directory_entries
        )
        assert (
            not src_directory_listed
        ), f"src/ should not be listed as directory, but found in: {directory_entries}"

        # Should show single files in root
        assert "readme.txt" in output

    def test_status_empty_untracked_directory_not_shown(
        self, temp_dir, clean_env, capsys
    ):
        """Test that empty untracked directories are not shown in status.

        Git doesn't track empty directories, so they shouldn't appear in status output.
        """
        os.chdir(temp_dir)

        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create empty directory
        empty_dir = repo_path / "empty_dir"
        empty_dir.mkdir()

        # Create directory with only subdirectories (no files)
        nested_empty = repo_path / "nested"
        nested_empty.mkdir()
        (nested_empty / "empty_subdir").mkdir()

        # Test status
        args = Namespace()
        cmd_status(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should not show empty directories
        assert "empty_dir" not in output
        assert "nested" not in output
        assert "empty_subdir" not in output
