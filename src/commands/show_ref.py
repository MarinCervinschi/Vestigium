from argparse import Namespace

from src.core.refs import RefDict, ref_list
from src.core.repository import VesRepository, repo_find


def cmd_show_ref(_) -> None:
    """
    CLI command to display all references in the repository.

    This command is the entry point for the 'show-ref' CLI command.
    It finds the current repository, retrieves all references, and
    displays them in a human-readable format with their SHA hashes.

    Output:
        Prints all references in the format:
        {sha_hash} refs/{category}/{ref_name}

    Example output:
        abc123... refs/heads/master
        def456... refs/heads/develop
        789abc... refs/tags/v1.0
        012def... refs/remotes/origin/master
    """
    repo = repo_find()
    assert repo is not None
    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")


def show_ref(
    repo: VesRepository,
    refs: RefDict,
    with_hash=True,
    prefix: str = "",
) -> None:
    """
    Recursively display Ves references with their SHA hashes and full paths.

    This function traverses the nested reference structure and prints each
    reference with its SHA hash and full path. It handles the recursive
    nature of the refs directory structure (heads/, tags/, remotes/, etc.).

    Args:
        repo (VesRepository): The repository containing the references
        refs (RefDict): Nested dictionary of references from ref_list()
        with_hash (bool): Whether to include SHA hashes in output (default: True)
        prefix (str): Path prefix for building full reference names (default: "")

    Output formats:
        - With hash: "{sha_hash} {full_ref_path}"
        - Without hash: "{full_ref_path}"

    Behavior:
        - For string values (SHA hashes): prints the reference
        - For dict values (subdirectories): recursively processes contents
        - For None values (unresolvable refs): skips silently
        - Builds full paths by concatenating prefixes with ref names

    Note:
        The function uses isinstance() to handle the Union type from RefDict,
        distinguishing between SHA strings and nested dictionaries.
    """
    if prefix:
        prefix = prefix + "/"

    for k, v in refs.items():
        if isinstance(v, str) and with_hash:
            print(f"{v} {prefix}{k}")
        elif isinstance(v, str):
            print(f"{prefix}{k}")
        elif isinstance(v, dict):
            show_ref(repo, v, with_hash=with_hash, prefix=f"{prefix}{k}")
        # Note: None values (unresolvable refs) are silently skipped
