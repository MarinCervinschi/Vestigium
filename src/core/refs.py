import os
from typing import Dict, Optional, Union

from src.core.repository import VesRepository, repo_dir, repo_file

# Type alias for recursive reference structure
RefDict = Dict[str, Union[str, None, "RefDict"]]


def ref_resolve(repo: VesRepository, ref: str) -> Optional[str]:
    """
    Resolve a Ves reference to its final SHA hash.

    Ves references can be either direct (containing a SHA hash) or symbolic
    (containing "ref: path/to/another/ref"). This function recursively follows
    symbolic references until it finds a concrete SHA hash.

    Args:
        repo (VesRepository): The repository to search for references
        ref (str): Reference path to resolve (e.g., "HEAD", "refs/heads/master")

    Returns:
        Optional[str]: The SHA hash the reference points to, or None if the
                      reference doesn't exist or cannot be resolved

    Reference formats:
        - Direct: "abc123..." (40-character SHA hash)
        - Symbolic: "ref: refs/heads/master" (points to another reference)

    Note:
        This function handles the recursive resolution of symbolic references,
        which is common in Ves (e.g., HEAD -> refs/heads/master -> commit SHA).
    """
    path = repo_file(repo, ref)

    if path is None or not os.path.isfile(path):
        return None

    with open(path, "r") as fp:
        data = fp.read()[:-1]  # Remove trailing newline

    if data.startswith("ref: "):
        # Symbolic reference: recursively resolve the target
        return ref_resolve(repo, data[5:])
    else:
        # Direct reference: return the SHA hash
        return data


def ref_list(repo: VesRepository, path: Optional[str] = None) -> RefDict:
    """
    Recursively list all Ves references in a directory.

    This function traverses the refs directory structure and builds a nested
    dictionary containing all references. It handles both files (individual refs)
    and subdirectories (ref namespaces like heads/, tags/, remotes/).

    Args:
        repo (VesRepository): The repository to list references from
        path (Optional[str]): Starting directory path. If None, starts from
                             the repository's refs directory

    Returns:
        RefDict: Nested dictionary structure representing the refs hierarchy.
                Keys are ref names/directories, values can be:
                - str: SHA hash for direct references
                - None: For unresolvable references
                - RefDict: Nested dictionary for subdirectories

    Structure example:
        {
            "heads": {
                "master": "abc123...",
                "develop": "def456..."
            },
            "tags": {
                "v1.0": "789abc..."
            },
            "remotes": {
                "origin": {
                    "master": "abc123..."
                }
            }
        }

    Note:
        The function sorts entries alphabetically for consistent output.
        Each reference file is resolved using ref_resolve() to get its final SHA.
    """
    if not path:
        path = repo_dir(repo, "refs")

    if path is None:
        return dict()

    ret = dict()

    for f in sorted(os.listdir(path)):
        can = os.path.join(path, f)
        if os.path.isdir(can):
            # Subdirectory: recursively list its contents
            ret[f] = ref_list(repo, can)
        else:
            # File: resolve the reference to its SHA
            ret[f] = ref_resolve(repo, can)

    return ret
