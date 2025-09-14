from argparse import Namespace

from src.core.objects import object_find
from src.core.repository import repo_find


def cmd_rev_parse(args: Namespace) -> None:
    """
    Resolves and prints the object ID for a given name in the repository.

    Args:
        args (Namespace): Command-line arguments containing:
            - name (str): The name or reference to resolve.
            - type (Optional[str]): The expected object type (e.g., 'commit', 'tree', 'blob').

    Behavior:
        - Encodes the type if provided.
        - Finds the repository.
        - If the repository is found, prints the object ID corresponding to the given name and type.
        - If the repository is not found, does nothing.
    """
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    repo = repo_find()
    assert repo is not None

    print(object_find(repo, args.name, fmt, follow=True))
