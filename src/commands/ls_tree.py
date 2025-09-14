import os
from argparse import Namespace

from src.core.objects import VesTree, object_find, object_read
from src.core.repository import VesRepository, repo_find


def cmd_ls_tree(args: Namespace) -> None:
    """
    CLI command to list the contents of a tree object.

    This command is the entry point for the 'ls-tree' CLI command.
    It finds the current repository and delegates to the ls_tree function
    to display the contents of the specified tree object.

    Args:
        args (Namespace): Command line arguments containing:
                         - tree: SHA or reference to the tree object
                         - recursive: Whether to recursively list subdirectories
    """
    repo = repo_find()
    assert repo is not None
    ls_tree(repo, args.tree, args.recursive)


def ls_tree(
    repo: VesRepository, ref: str, recursive: bool = False, prefix: str = ""
) -> None:
    """
    List the contents of a tree object in the repository.

    This function reads a tree object and displays its contents in a format
    similar to 'ls -l'. Each entry shows the file mode, object type, SHA hash,
    and path. Can optionally recurse into subdirectories.

    Args:
        repo (VesRepository): The repository to read from
        ref (str): SHA hash or reference to the tree object
        recursive (bool): If True, recursively list subdirectory contents
        prefix (str): Path prefix for nested directories (used internally)

    Output format:
        {mode} {type} {sha}\t{path}

    Object types:
        - tree: Directory
        - blob: Regular file or symlink
        - commit: Submodule reference

    Note:
        File modes are normalized to 6 digits (padded with leading zeros).
        The function handles various Ves object modes including regular files,
        symlinks, directories, and submodules.
    """
    sha = object_find(repo, ref, fmt=b"tree")
    if sha is None:
        return
    obj = object_read(repo, sha)
    if obj is None:
        return

    assert isinstance(obj, VesTree)

    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type:
            case b"04":
                type = "tree"  # Directory
            case b"10":
                type = "blob"  # Regular file
            case b"12":
                type = "blob"  # Symlink (contents is link target)
            case b"16":
                type = "commit"  # Submodule reference
            case _:
                raise Exception(f"Weird tree leaf mode {item.mode}")

        if not (recursive and type == "tree"):
            # Leaf node: print the entry
            print(
                f"{'0' * (6 - len(item.mode)) + item.mode.decode('ascii')} {type} {item.sha}\t{os.path.join(prefix, item.path)}"
            )
        else:
            # Directory node with recursive flag: recurse into subdirectory
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))
