from argparse import Namespace
from src.core.repository import repo_find
import os
from src.core.index import index_read, index_write
from src.core.repository import VesRepository


def cmd_rm(args: Namespace) -> None:
    """
    Command line interface for removing files from the Vestigium repository.

    This function serves as the entry point for the 'ves rm' command. It locates
    the repository and delegates the actual removal operation to the rm() function.

    Args:
        args: Parsed command line arguments containing the paths to remove

    Note:
        If no repository is found in the current directory or its parents,
        the function returns silently without performing any operation.
    """
    repo = repo_find()
    if repo is None:
        return
    rm(repo, args.path)


def rm(
    repo: VesRepository,
    paths: list[str],
    delete: bool = True,
    skip_missing: bool = False,
) -> None:
    """
    Remove files from the Vestigium index and optionally from the filesystem.

    This function removes the specified files from the repository index (staging area)
    and optionally deletes them from the filesystem. It ensures that only files within
    the repository worktree can be removed and validates that all specified paths
    exist in the index before proceeding.

    The removal process:
    1. Validates all paths are within the repository worktree
    2. Finds matching entries in the index
    3. Updates the index by removing matched entries
    4. Optionally deletes the physical files from the filesystem
    5. Writes the updated index back to disk

    Args:
        repo: The VesRepository instance to operate on
        paths: List of file paths to remove (can be relative or absolute)
        delete: If True, also delete files from filesystem (default: True)
        skip_missing: If True, ignore paths not found in index (default: False)

    Raises:
        Exception: If any path is outside the repository worktree
        Exception: If any path is not in the index and skip_missing is False
        OSError: If filesystem deletion fails when delete=True

    Note:
        Files are removed from the index even if filesystem deletion fails.
        Use delete=False to only remove from index without touching filesystem.
    """
    index = index_read(repo)

    worktree = repo.worktree + os.sep

    # Validate paths and make them absolute
    abspaths = set()
    for path in paths:
        abspath = os.path.abspath(path)
        if abspath.startswith(worktree):
            abspaths.add(abspath)
        else:
            raise Exception(f"Cannot remove paths outside of worktree: {paths}")

    kept_entries = list()
    remove = list()

    # Filter entries: keep those not being removed
    for e in index.entries:
        full_path = os.path.join(repo.worktree, e.name)

        if full_path in abspaths:
            remove.append(full_path)
            abspaths.remove(full_path)
        else:
            kept_entries.append(e)

    # Check if any paths weren't found in the index
    if len(abspaths) > 0 and not skip_missing:
        raise Exception(f"Cannot remove paths not in the index: {abspaths}")

    # Delete files from filesystem if requested
    if delete:
        for path in remove:
            os.unlink(path)

    # Update index with remaining entries
    index.entries = kept_entries
    index_write(repo, index)
