from argparse import Namespace

from src.core.repository import repo_find
from src.utils.ignore import check_ignore, vesignore_read


def cmd_check_ignore(args: Namespace) -> None:
    """
    Checks if the specified paths are ignored according to the repository's ignore rules.

    Args:
        args (Namespace): Command-line arguments containing a list of paths to check.

    Returns:
        None

    Side Effects:
        Prints each path that is ignored by the repository's ignore rules.
    """
    repo = repo_find()
    assert repo is not None
    rules = vesignore_read(repo)
    if rules is None:
        return
    for path in args.path:
        if check_ignore(rules, path):
            print(path)
