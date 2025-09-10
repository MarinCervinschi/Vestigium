from src.core.repository import repo_create
from argparse import Namespace


def cmd_init(args: Namespace) -> None:
    """
    Handles the 'init' command for Vestigium CLI.

    Initializes a new, empty repository at the specified path.
    Args:
        args (Namespace): Parsed command-line arguments. Must contain 'path'.
    """
    repo_create(args.path)
