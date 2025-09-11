from argparse import Namespace

from src.core.objects import object_hash
from src.core.repository import repo_find


def cmd_hash_object(args: Namespace) -> None:
    """Hash an object and optionally write it to the repository.

    Args:
        args (Namespace): Command-line arguments containing:
            - path (str): Path to the file to hash.
            - type (str): Type of the object (e.g., 'blob', 'tree').
            - write (bool): Whether to write the object to the repository.

    Returns:
        None. Prints the SHA-1 hash of the object.
    """
    if args.write:
        repo = repo_find()
    else:
        repo = None

    with open(args.path, "rb") as fd:
        sha = object_hash(fd, args.type.encode(), repo)
        print(sha)
