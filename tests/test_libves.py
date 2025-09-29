import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.libves import argparser, main


class TestLibves:
    """Test cases for the main libves module and CLI interface."""

    def test_argument_parser_init_command(self):
        """Test that the argument parser correctly parses init command."""
        # Test with default path
        args = argparser.parse_args(["init"])
        assert args.command == "init"
        assert args.path == "."

        # Test with specified path
        args = argparser.parse_args(["init", "/tmp/test_repo"])
        assert args.command == "init"
        assert args.path == "/tmp/test_repo"

    def test_argument_parser_add_command(self):
        """Test that the argument parser correctly parses add command."""
        args = argparser.parse_args(["add", "file1.txt", "file2.txt"])
        assert args.command == "add"
        assert args.path == ["file1.txt", "file2.txt"]

    def test_argument_parser_commit_command(self):
        """Test that the argument parser correctly parses commit command."""
        args = argparser.parse_args(["commit", "-m", "Test commit message"])
        assert args.command == "commit"
        assert args.message == "Test commit message"

    def test_argument_parser_cat_file_command(self):
        """Test that the argument parser correctly parses cat-file command."""
        args = argparser.parse_args(["cat-file", "blob", "abc123"])
        assert args.command == "cat-file"
        assert args.type == "blob"
        assert args.object == "abc123"

    def test_argument_parser_hash_object_command(self):
        """Test that the argument parser correctly parses hash-object command."""
        # Test without write flag
        args = argparser.parse_args(["hash-object", "test.txt"])
        assert args.command == "hash-object"
        assert args.type == "blob"  # default
        assert args.write == False
        assert args.path == "test.txt"

        # Test with write flag and type
        args = argparser.parse_args(["hash-object", "-w", "-t", "blob", "test.txt"])
        assert args.command == "hash-object"
        assert args.type == "blob"
        assert args.write == True
        assert args.path == "test.txt"

    def test_argument_parser_log_command(self):
        """Test that the argument parser correctly parses log command."""
        # Test with default HEAD
        args = argparser.parse_args(["log"])
        assert args.command == "log"
        assert args.commit == "HEAD"

        # Test with specific commit
        args = argparser.parse_args(["log", "abc123"])
        assert args.command == "log"
        assert args.commit == "abc123"

    def test_argument_parser_ls_tree_command(self):
        """Test that the argument parser correctly parses ls-tree command."""
        # Test without recursive flag
        args = argparser.parse_args(["ls-tree", "abc123"])
        assert args.command == "ls-tree"
        assert args.recursive == False
        assert args.tree == "abc123"

        # Test with recursive flag
        args = argparser.parse_args(["ls-tree", "-r", "abc123"])
        assert args.command == "ls-tree"
        assert args.recursive == True
        assert args.tree == "abc123"

    def test_argument_parser_checkout_command(self):
        """Test that the argument parser correctly parses checkout command."""
        args = argparser.parse_args(["checkout", "abc123", "/tmp/checkout"])
        assert args.command == "checkout"
        assert args.commit == "abc123"
        assert args.path == "/tmp/checkout"

    def test_argument_parser_show_ref_command(self):
        """Test that the argument parser correctly parses show-ref command."""
        args = argparser.parse_args(["show-ref"])
        assert args.command == "show-ref"

    def test_argument_parser_tag_command(self):
        """Test that the argument parser correctly parses tag command."""
        # Test list tags (no arguments)
        args = argparser.parse_args(["tag"])
        assert args.command == "tag"
        assert args.create_tag_object == False
        assert args.name is None
        assert args.object == "HEAD"

        # Test create lightweight tag
        args = argparser.parse_args(["tag", "v1.0"])
        assert args.command == "tag"
        assert args.create_tag_object == False
        assert args.name == "v1.0"
        assert args.object == "HEAD"

        # Test create annotated tag
        args = argparser.parse_args(["tag", "-a", "v1.0", "abc123"])
        assert args.command == "tag"
        assert args.create_tag_object == True
        assert args.name == "v1.0"
        assert args.object == "abc123"

    def test_argument_parser_rev_parse_command(self):
        """Test that the argument parser correctly parses rev-parse command."""
        # Test without type specification
        args = argparser.parse_args(["rev-parse", "HEAD"])
        assert args.command == "rev-parse"
        assert args.type is None
        assert args.name == "HEAD"

        # Test with type specification
        args = argparser.parse_args(["rev-parse", "--ves-type", "commit", "HEAD"])
        assert args.command == "rev-parse"
        assert args.type == "commit"
        assert args.name == "HEAD"

    def test_argument_parser_ls_files_command(self):
        """Test that the argument parser correctly parses ls-files command."""
        # Test without verbose flag
        args = argparser.parse_args(["ls-files"])
        assert args.command == "ls-files"
        assert args.verbose == False

        # Test with verbose flag
        args = argparser.parse_args(["ls-files", "--verbose"])
        assert args.command == "ls-files"
        assert args.verbose == True

    def test_argument_parser_check_ignore_command(self):
        """Test that the argument parser correctly parses check-ignore command."""
        args = argparser.parse_args(["check-ignore", "file1.txt", "dir/file2.txt"])
        assert args.command == "check-ignore"
        assert args.path == ["file1.txt", "dir/file2.txt"]

    def test_argument_parser_status_command(self):
        """Test that the argument parser correctly parses status command."""
        args = argparser.parse_args(["status"])
        assert args.command == "status"

    def test_argument_parser_rm_command(self):
        """Test that the argument parser correctly parses rm command."""
        args = argparser.parse_args(["rm", "file1.txt", "file2.txt"])
        assert args.command == "rm"
        assert args.path == ["file1.txt", "file2.txt"]

    @patch("src.commands.init.cmd_init")
    def test_main_calls_init_command(self, mock_cmd_init, temp_dir, clean_env):
        """Test that main() correctly calls the init command."""
        main(["init", str(temp_dir)])
        mock_cmd_init.assert_called_once()

        # Verify the arguments passed to cmd_init
        call_args = mock_cmd_init.call_args[0][0]
        assert call_args.command == "init"
        assert call_args.path == str(temp_dir)

    @patch("src.commands.add.cmd_add")
    def test_main_calls_add_command(self, mock_cmd_add):
        """Test that main() correctly calls the add command."""
        main(["add", "file1.txt", "file2.txt"])
        mock_cmd_add.assert_called_once()

        # Verify the arguments passed to cmd_add
        call_args = mock_cmd_add.call_args[0][0]
        assert call_args.command == "add"
        assert call_args.path == ["file1.txt", "file2.txt"]

    @patch("src.commands.commit.cmd_commit")
    def test_main_calls_commit_command(self, mock_cmd_commit):
        """Test that main() correctly calls the commit command."""
        main(["commit", "-m", "Test message"])
        mock_cmd_commit.assert_called_once()

        # Verify the arguments passed to cmd_commit
        call_args = mock_cmd_commit.call_args[0][0]
        assert call_args.command == "commit"
        assert call_args.message == "Test message"

    @patch("src.commands.cat_file.cmd_cat_file")
    def test_main_calls_cat_file_command(self, mock_cmd_cat_file):
        """Test that main() correctly calls the cat-file command."""
        main(["cat-file", "blob", "abc123"])
        mock_cmd_cat_file.assert_called_once()

        # Verify the arguments passed to cmd_cat_file
        call_args = mock_cmd_cat_file.call_args[0][0]
        assert call_args.command == "cat-file"
        assert call_args.type == "blob"
        assert call_args.object == "abc123"

    @patch("src.commands.hash_object.cmd_hash_object")
    def test_main_calls_hash_object_command(self, mock_cmd_hash_object):
        """Test that main() correctly calls the hash-object command."""
        main(["hash-object", "-w", "test.txt"])
        mock_cmd_hash_object.assert_called_once()

        # Verify the arguments passed to cmd_hash_object
        call_args = mock_cmd_hash_object.call_args[0][0]
        assert call_args.command == "hash-object"
        assert call_args.write == True
        assert call_args.path == "test.txt"

    @patch("src.commands.log.cmd_log")
    def test_main_calls_log_command(self, mock_cmd_log):
        """Test that main() correctly calls the log command."""
        main(["log", "HEAD"])
        mock_cmd_log.assert_called_once()

        # Verify the arguments passed to cmd_log
        call_args = mock_cmd_log.call_args[0][0]
        assert call_args.command == "log"
        assert call_args.commit == "HEAD"

    @patch("src.commands.ls_tree.cmd_ls_tree")
    def test_main_calls_ls_tree_command(self, mock_cmd_ls_tree):
        """Test that main() correctly calls the ls-tree command."""
        main(["ls-tree", "-r", "abc123"])
        mock_cmd_ls_tree.assert_called_once()

        # Verify the arguments passed to cmd_ls_tree
        call_args = mock_cmd_ls_tree.call_args[0][0]
        assert call_args.command == "ls-tree"
        assert call_args.recursive == True
        assert call_args.tree == "abc123"

    @patch("src.commands.checkout.cmd_checkout")
    def test_main_calls_checkout_command(self, mock_cmd_checkout):
        """Test that main() correctly calls the checkout command."""
        main(["checkout", "abc123", "/tmp/dest"])
        mock_cmd_checkout.assert_called_once()

        # Verify the arguments passed to cmd_checkout
        call_args = mock_cmd_checkout.call_args[0][0]
        assert call_args.command == "checkout"
        assert call_args.commit == "abc123"
        assert call_args.path == "/tmp/dest"

    @patch("src.commands.show_ref.cmd_show_ref")
    def test_main_calls_show_ref_command(self, mock_cmd_show_ref):
        """Test that main() correctly calls the show-ref command."""
        main(["show-ref"])
        mock_cmd_show_ref.assert_called_once()

        # Verify the arguments passed to cmd_show_ref
        call_args = mock_cmd_show_ref.call_args[0][0]
        assert call_args.command == "show-ref"

    @patch("src.commands.tag.cmd_tag")
    def test_main_calls_tag_command(self, mock_cmd_tag):
        """Test that main() correctly calls the tag command."""
        main(["tag", "-a", "v1.0"])
        mock_cmd_tag.assert_called_once()

        # Verify the arguments passed to cmd_tag
        call_args = mock_cmd_tag.call_args[0][0]
        assert call_args.command == "tag"
        assert call_args.create_tag_object == True
        assert call_args.name == "v1.0"

    @patch("src.commands.rev_parse.cmd_rev_parse")
    def test_main_calls_rev_parse_command(self, mock_cmd_rev_parse):
        """Test that main() correctly calls the rev-parse command."""
        main(["rev-parse", "--ves-type", "commit", "HEAD"])
        mock_cmd_rev_parse.assert_called_once()

        # Verify the arguments passed to cmd_rev_parse
        call_args = mock_cmd_rev_parse.call_args[0][0]
        assert call_args.command == "rev-parse"
        assert call_args.type == "commit"
        assert call_args.name == "HEAD"

    @patch("src.commands.ls_files.cmd_ls_files")
    def test_main_calls_ls_files_command(self, mock_cmd_ls_files):
        """Test that main() correctly calls the ls-files command."""
        main(["ls-files", "--verbose"])
        mock_cmd_ls_files.assert_called_once()

        # Verify the arguments passed to cmd_ls_files
        call_args = mock_cmd_ls_files.call_args[0][0]
        assert call_args.command == "ls-files"
        assert call_args.verbose == True

    @patch("src.commands.check_ignore.cmd_check_ignore")
    def test_main_calls_check_ignore_command(self, mock_cmd_check_ignore):
        """Test that main() correctly calls the check-ignore command."""
        main(["check-ignore", "file1.txt", "dir/file2.txt"])
        mock_cmd_check_ignore.assert_called_once()

        # Verify the arguments passed to cmd_check_ignore
        call_args = mock_cmd_check_ignore.call_args[0][0]
        assert call_args.command == "check-ignore"
        assert call_args.path == ["file1.txt", "dir/file2.txt"]

    @patch("src.commands.status.cmd_status")
    def test_main_calls_status_command(self, mock_cmd_status):
        """Test that main() correctly calls the status command."""
        main(["status"])
        mock_cmd_status.assert_called_once()

        # Verify the arguments passed to cmd_status
        call_args = mock_cmd_status.call_args[0][0]
        assert call_args.command == "status"

    @patch("src.commands.rm.cmd_rm")
    def test_main_calls_rm_command(self, mock_cmd_rm):
        """Test that main() correctly calls the rm command."""
        main(["rm", "file1.txt", "file2.txt"])
        mock_cmd_rm.assert_called_once()

        # Verify the arguments passed to cmd_rm
        call_args = mock_cmd_rm.call_args[0][0]
        assert call_args.command == "rm"
        assert call_args.path == ["file1.txt", "file2.txt"]

    def test_main_bad_command(self, capsys):
        """Test that main() handles unknown commands gracefully."""
        # Since the parser doesn't recognize unknown commands, this will cause a SystemExit
        with pytest.raises(SystemExit):
            main(["unknown-command"])

    @patch("builtins.print")
    def test_main_bad_command_with_mock_parser(self, mock_print):
        """Test the default case in the match statement."""
        # We need to test the case where the parser accepts a command but it's not in our match statement
        # This is a bit tricky since all valid commands are in the match statement
        # We can mock the argument parsing to return an unknown command

        from argparse import Namespace

        with patch("src.libves.argparser") as mock_parser:
            mock_args = Namespace()
            mock_args.command = "unknown-internal-command"
            mock_parser.parse_args.return_value = mock_args

            main(["fake-args"])
            mock_print.assert_called_once_with("Bad command.")

    def test_main_integration_init_and_add(self, temp_dir, clean_env):
        """Integration test: init a repository and add a file."""
        os.chdir(temp_dir)

        # Initialize repository
        repo_path = Path(temp_dir) / "integration_repo"
        main(["init", str(repo_path)])

        # Verify repository was created
        assert repo_path.exists()
        assert (repo_path / ".ves").exists()

        # Change to the repository directory
        os.chdir(repo_path)

        # Create a file and add it
        test_file = repo_path / "test.txt"
        test_file.write_text("Integration test content")

        # Add the file (this should work without errors)
        main(["add", "test.txt"])

        # Verify file was added to index (basic check)
        index_file = repo_path / ".ves" / "index"
        assert index_file.exists()

    def test_main_no_arguments_fails(self):
        """Test that main() fails gracefully with no arguments."""
        with pytest.raises(SystemExit):
            main([])

    def test_main_help_argument(self, capsys):
        """Test that main() shows help when --help is provided."""
        with pytest.raises(SystemExit):
            main(["--help"])

        captured = capsys.readouterr()
        assert "Vestigium - A Version Control System" in captured.out

    @patch("src.commands.init.cmd_init")
    def test_main_function_signature_default(self, mock_cmd_init):
        """Test that main() function has the correct default parameter behavior."""
        # The function signature is main(argv: List[str] = sys.argv[1:])
        # We test that it works correctly when called with explicit arguments
        main(["init", "/tmp/test"])
        mock_cmd_init.assert_called_once()

        # Verify the arguments passed to cmd_init
        call_args = mock_cmd_init.call_args[0][0]
        assert call_args.command == "init"
        assert call_args.path == "/tmp/test"

    def test_main_empty_argv_uses_sys_argv(self):
        """Test that main() with empty list uses the empty list, not sys.argv."""
        # Empty list should cause a SystemExit because no command is provided
        with pytest.raises(SystemExit):
            main([])  # Empty list should fail

    def test_argument_parser_required_subcommand(self):
        """Test that the argument parser requires a subcommand."""
        with pytest.raises(SystemExit):
            argparser.parse_args([])

    def test_argument_parser_invalid_cat_file_type(self):
        """Test that invalid types for cat-file are rejected."""
        with pytest.raises(SystemExit):
            argparser.parse_args(["cat-file", "invalid", "abc123"])

    def test_argument_parser_invalid_hash_object_type(self):
        """Test that invalid types for hash-object are rejected."""
        with pytest.raises(SystemExit):
            argparser.parse_args(["hash-object", "-t", "invalid", "test.txt"])

    def test_argument_parser_invalid_rev_parse_type(self):
        """Test that invalid types for rev-parse are rejected."""
        with pytest.raises(SystemExit):
            argparser.parse_args(["rev-parse", "--ves-type", "invalid", "HEAD"])

    def test_argument_parser_check_ignore_requires_paths(self):
        """Test that check-ignore requires at least one path."""
        with pytest.raises(SystemExit):
            argparser.parse_args(["check-ignore"])

    def test_argument_parser_rm_requires_paths(self):
        """Test that rm requires at least one path."""
        with pytest.raises(SystemExit):
            argparser.parse_args(["rm"])

    def test_argument_parser_add_requires_paths(self):
        """Test that add requires at least one path."""
        with pytest.raises(SystemExit):
            argparser.parse_args(["add"])
