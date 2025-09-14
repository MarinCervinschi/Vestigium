import os
from argparse import Namespace
from pathlib import Path

import pytest

from src.commands.check_ignore import cmd_check_ignore
from src.commands.init import cmd_init
from src.commands.add import cmd_add
from src.commands.commit import cmd_commit
from src.core.repository import repo_find
from src.utils.ignore import vesignore_read, check_ignore, VesIgnore


class TestCheckIgnoreCommand:
    """Test cases for the check-ignore command."""

    def test_check_ignore_no_rules(self, temp_dir, clean_env, capsys):
        """Test check-ignore when no ignore rules exist."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Check some paths (should produce no output)
        args = Namespace(path=["test.txt", "src/main.py", "docs/readme.md"])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    def test_check_ignore_with_vesignore_file(self, temp_dir, clean_env, capsys):
        """Test check-ignore with .vesignore file in repository."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create .vesignore file
        vesignore_file = repo_path / ".vesignore"
        vesignore_content = """# Ignore patterns
*.log
*.tmp
build/
src/*.pyc
"""
        vesignore_file.write_text(vesignore_content)

        # Add .vesignore to index
        add_args = Namespace(path=[".vesignore"])
        cmd_add(add_args)
        
        commit_args = Namespace(message="Add ignore rules")
        cmd_commit(commit_args)

        # Test various paths
        args = Namespace(path=[
            "app.log",           # Should be ignored (*.log)
            "temp.tmp",          # Should be ignored (*.tmp)
            "build/output.exe",  # Should be ignored (build/)
            "src/test.pyc",      # Should be ignored (src/*.pyc)
            "src/main.py",       # Should NOT be ignored
            "README.md",         # Should NOT be ignored
        ])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "app.log" in ignored_paths
        assert "temp.tmp" in ignored_paths
        assert "build/output.exe" in ignored_paths
        assert "src/test.pyc" in ignored_paths
        assert "src/main.py" not in ignored_paths
        assert "README.md" not in ignored_paths

    def test_check_ignore_with_negation_rules(self, temp_dir, clean_env, capsys):
        """Test check-ignore with negation rules (!)."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create .vesignore with negation rules
        vesignore_file = repo_path / ".vesignore"
        vesignore_content = """# Ignore all .log files
*.log
# But don't ignore important.log
!important.log
# Ignore build directory
build/
# But don't ignore build/keep.txt
!build/keep.txt
"""
        vesignore_file.write_text(vesignore_content)

        # Add .vesignore to index
        add_args = Namespace(path=[".vesignore"])
        cmd_add(add_args)
        
        commit_args = Namespace(message="Add negation rules")
        cmd_commit(commit_args)

        # Test paths with negation rules
        args = Namespace(path=[
            "debug.log",         # Should be ignored (*.log)
            "important.log",     # Should NOT be ignored (!important.log)
            "build/output.exe",  # Should be ignored (build/)
            "build/keep.txt",    # Should NOT be ignored (!build/keep.txt)
        ])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "debug.log" in ignored_paths
        assert "important.log" not in ignored_paths
        assert "build/output.exe" in ignored_paths
        assert "build/keep.txt" not in ignored_paths

    def test_check_ignore_with_local_exclude(self, temp_dir, clean_env, capsys):
        """Test check-ignore with local exclude file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create local exclude file
        exclude_dir = repo_path / ".ves" / "info"
        exclude_dir.mkdir(parents=True, exist_ok=True)
        exclude_file = exclude_dir / "exclude"
        exclude_content = """# Local exclude patterns
*.secret
private/
"""
        exclude_file.write_text(exclude_content)

        # Test paths
        args = Namespace(path=[
            "config.secret",     # Should be ignored (*.secret)
            "private/data.txt",  # Should be ignored (private/)
            "public/info.txt",   # Should NOT be ignored
        ])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "config.secret" in ignored_paths
        assert "private/data.txt" in ignored_paths
        assert "public/info.txt" not in ignored_paths

    def test_check_ignore_scoped_vesignore(self, temp_dir, clean_env, capsys):
        """Test check-ignore with scoped .vesignore files in subdirectories."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create subdirectory with its own .vesignore
        src_dir = repo_path / "src"
        src_dir.mkdir()
        src_vesignore = src_dir / ".vesignore"
        src_vesignore_content = """# Source-specific ignores
*.o
*.so
__pycache__/
"""
        src_vesignore.write_text(src_vesignore_content)

        # Add scoped .vesignore to index
        add_args = Namespace(path=["src/.vesignore"])
        cmd_add(add_args)
        
        commit_args = Namespace(message="Add scoped ignore rules")
        cmd_commit(commit_args)

        # Test paths in different scopes
        args = Namespace(path=[
            "src/main.o",        # Should be ignored (src scope: *.o)
            "src/lib.so",        # Should be ignored (src scope: *.so)
            "src/__pycache__/test.pyc",  # Should be ignored (src scope: __pycache__/)
            "docs/main.o",       # Should NOT be ignored (different scope)
            "src/main.py",       # Should NOT be ignored
        ])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "src/main.o" in ignored_paths
        assert "src/lib.so" in ignored_paths
        assert "src/__pycache__/test.pyc" in ignored_paths
        assert "docs/main.o" not in ignored_paths
        assert "src/main.py" not in ignored_paths

    def test_check_ignore_comments_and_empty_lines(self, temp_dir, clean_env, capsys):
        """Test that comments and empty lines in ignore files are handled correctly."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create .vesignore with comments and empty lines
        vesignore_file = repo_path / ".vesignore"
        vesignore_content = """
# This is a comment
*.log

# Another comment
*.tmp

# Empty lines should be ignored

*.bak
"""
        vesignore_file.write_text(vesignore_content)

        # Add .vesignore to index
        add_args = Namespace(path=[".vesignore"])
        cmd_add(add_args)
        
        commit_args = Namespace(message="Add ignore with comments")
        cmd_commit(commit_args)

        # Test paths
        args = Namespace(path=["test.log", "backup.bak", "temp.tmp"])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "test.log" in ignored_paths
        assert "backup.bak" in ignored_paths
        assert "temp.tmp" in ignored_paths

    def test_check_ignore_escape_characters(self, temp_dir, clean_env, capsys):
        """Test ignore rules with escape characters."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create .vesignore with escaped characters
        vesignore_file = repo_path / ".vesignore"
        vesignore_content = r"""# Escaped patterns
\#not-a-comment.txt
\!not-a-negation.txt
"""
        vesignore_file.write_text(vesignore_content)

        # Add .vesignore to index
        add_args = Namespace(path=[".vesignore"])
        cmd_add(add_args)
        
        commit_args = Namespace(message="Add escaped patterns")
        cmd_commit(commit_args)

        # Test escaped patterns
        args = Namespace(path=["#not-a-comment.txt", "!not-a-negation.txt"])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "#not-a-comment.txt" in ignored_paths
        assert "!not-a-negation.txt" in ignored_paths

    def test_check_ignore_without_repository(self, temp_dir, clean_env):
        """Test that check-ignore fails when not in a repository."""
        os.chdir(temp_dir)

        # Try to run check-ignore without repository
        args = Namespace(path=["test.txt"])

        with pytest.raises(Exception, match="No ves directory."):
            cmd_check_ignore(args)

    def test_check_ignore_empty_path_list(self, temp_dir, clean_env, capsys):
        """Test check-ignore with empty path list."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Check empty path list
        args = Namespace(path=[])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    def test_check_ignore_mixed_patterns(self, temp_dir, clean_env, capsys):
        """Test check-ignore with various pattern types."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        # Create .vesignore with different pattern types
        vesignore_file = repo_path / ".vesignore"
        vesignore_content = """# Various pattern types
*.log                    # Extension pattern
build/                   # Directory pattern
src/**/*.pyc             # Nested pattern
test_*.py               # Prefix pattern
**/node_modules/        # Anywhere pattern
"""
        vesignore_file.write_text(vesignore_content)

        # Add .vesignore to index
        add_args = Namespace(path=[".vesignore"])
        cmd_add(add_args)
        
        commit_args = Namespace(message="Add mixed patterns")
        cmd_commit(commit_args)

        # Test various paths
        args = Namespace(path=[
            "app.log",                    # Should be ignored (*.log)
            "build/output.exe",           # Should be ignored (build/)
            "src/deep/nested/cache.pyc",  # Should be ignored (src/**/*.pyc)
            "test_main.py",              # Should be ignored (test_*.py)
            "lib/node_modules/pkg/index.js", # Should be ignored (**/node_modules/)
            "main.py",                   # Should NOT be ignored
            "src/main.py",               # Should NOT be ignored
        ])
        cmd_check_ignore(args)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        ignored_paths = [line.strip() for line in output_lines if line.strip()]

        assert "app.log" in ignored_paths
        assert "build/output.exe" in ignored_paths
        assert "src/deep/nested/cache.pyc" in ignored_paths
        assert "test_main.py" in ignored_paths
        assert "lib/node_modules/pkg/index.js" in ignored_paths
        assert "main.py" not in ignored_paths
        assert "src/main.py" not in ignored_paths

    def test_vesignore_read_function(self, temp_dir, clean_env):
        """Test vesignore_read function directly."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "test_repo"
        init_args = Namespace(path=str(repo_path))
        cmd_init(init_args)
        os.chdir(repo_path)

        repo = repo_find()
        assert repo is not None

        # Initially no rules
        rules = vesignore_read(repo)
        assert rules is not None
        assert len(rules.absolute) == 0
        assert len(rules.scoped) == 0

        # Add local exclude file
        exclude_dir = repo_path / ".ves" / "info"
        exclude_dir.mkdir(parents=True, exist_ok=True)
        exclude_file = exclude_dir / "exclude"
        exclude_file.write_text("*.local\n")

        # Now should have absolute rules
        rules = vesignore_read(repo)
        assert rules is not None
        assert len(rules.absolute) == 1
        assert len(rules.scoped) == 0

    def test_check_ignore_function_direct(self, temp_dir, clean_env):
        """Test check_ignore function directly."""
        # Create mock ignore rules
        rules = VesIgnore()
        rules.absolute = [[("*.log", True), ("*.tmp", True)]]
        rules.scoped = {"src": [("*.pyc", True)]}

        # Test various paths
        assert check_ignore(rules, "app.log") == True
        assert check_ignore(rules, "temp.tmp") == True
        assert check_ignore(rules, "src/main.pyc") == True
        assert check_ignore(rules, "main.py") == False
        assert check_ignore(rules, "docs/readme.md") == False

        # Test absolute path should raise exception
        with pytest.raises(Exception, match="requires path to be relative"):
            check_ignore(rules, "/absolute/path.txt")