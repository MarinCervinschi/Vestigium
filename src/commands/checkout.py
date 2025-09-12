import os
from argparse import Namespace

from src.core.objects import VesCommit, VesTree, object_find, object_read
from src.core.repository import repo_find
from src.utils.tree import tree_checkout


def cmd_checkout(args: Namespace) -> None:
    """
    CLI command to extract files from a commit or tree to a directory.

    This command checks out (extracts) all files from a specified commit or tree
    object and writes them to the filesystem at the given path. It's the inverse
    operation of commit: instead of saving files to the repository, it restores
    files from the repository to a working directory.

    Args:
        args (Namespace): Command line arguments containing:
                         - commit: SHA hash or reference to commit/tree to checkout
                         - path: Destination directory path where files will be extracted

    Behavior:
        - If given a commit, extracts the associated tree
        - If given a tree directly, extracts that tree
        - Destination must be empty directory or non-existent path
        - Creates destination directory if it doesn't exist
        - Recursively extracts all files and subdirectories

    Raises:
        Exception: If destination exists but is not a directory, or if directory is not empty
    """
    repo = repo_find()
    if repo is None:
        return

    sha = object_find(repo, args.commit)
    if sha is None:
        return
    obj = object_read(repo, sha)
    if obj is None:
        return

    if obj.fmt == b"commit":
        assert isinstance(obj, VesCommit)
        obj = object_read(repo, obj.kvlm[b"tree"].decode("ascii"))

    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception(f"Not a directory {args.path}!")
        if os.listdir(args.path):
            raise Exception(f"Not empty {args.path}!")
    else:
        os.makedirs(args.path)

    assert isinstance(obj, VesTree)
    tree_checkout(repo, obj, os.path.realpath(args.path))
