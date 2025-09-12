import sys
from argparse import Namespace
from typing import Optional

from src.core.objects import object_find, object_read
from src.core.repository import VesRepository, repo_find


def cmd_cat_file(args: Namespace) -> None:
    """CLI command to display the content of a Ves object.

    This command is the entry point for the 'cat-file' CLI command.
    It finds the current repository and delegates to the cat_file method to display
    the content of the specified object.

    Args:
        args (Namespace): Command line arguments containing:
            - object: Name or hash of the object to display
            - type: Type of the object (blob, tree, commit, tag)

    Returns:
        None: Prints the object content to stdout or an error message

    """
    repo = repo_find()
    if repo is None:
        return
    cat_file(repo, args.object, fmt=args.type.encode())


def cat_file(repo: VesRepository, obj: str, fmt: Optional[bytes] = None) -> None:
    """Display the content of a Ves object in the repository.

    This function searches for an object in the repository using the provided name or hash,
    reads it from disk and prints its serialized content to stdout.
    It's the core implementation of Ves 'cat-file' command.

    Args:
        repo (VesRepository): The Ves repository to search for the object
        obj (str): Name, partial hash or object to display.
            If None, the function returns without errors
        fmt (Optional[bytes], optional): Expected object type (blob, tree, commit, tag).
            If specified, used to disambiguate objects with similar hashes.
            Defaults to None (accepts any type)

    Returns:
        None: Prints the serialized object content to stdout

    Raises:
        No exceptions are raised directly, but prints error messages
        if the object is not found or cannot be read
    """
    sha = object_find(repo, obj, fmt=fmt)
    if sha is None:
        return
    obj_read = object_read(repo, sha)
    if obj_read is None:
        return
    sys.stdout.buffer.write(obj_read.serialize())
