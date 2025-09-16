import os
from src.core.index import VesIndex, index_read, index_write
from src.core.repository import VesRepository


def rm_in_memory(
    index: VesIndex,
    repo: VesRepository,
    paths: list[str],
    delete: bool = True,
    skip_missing: bool = False,
) -> None:
    """
    Remove files from the index (in-memory operation only).

    This is an optimized version of the rm function that works directly
    on an in-memory index object without reading/writing to disk.

    Args:
        index: The VesIndex object to modify
        repo: The VesRepository instance
        paths: List of file paths to remove
        delete: If True, also delete files from filesystem
        skip_missing: If True, ignore paths not found in index
    """
    worktree = repo.worktree + os.sep

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

    if len(abspaths) > 0 and not skip_missing:
        raise Exception(f"Cannot remove paths not in the index: {abspaths}")

    if delete:
        for path in remove:
            os.unlink(path)

    index.entries = kept_entries


class IndexTransaction:
    """
    Context manager for index transactions.

    This class provides transactional semantics for index operations:
    - Reads the index once at the beginning
    - Allows multiple operations on the in-memory index
    - Writes the index once at the end (only if no exceptions occurred)
    - Provides automatic rollback on exceptions

    Usage:
        with IndexTransaction(repo) as index:
            # Perform multiple operations on index
            rm_in_memory(index, paths1)
            add_in_memory(index, paths2)
            # Index is automatically written at the end
    """

    def __init__(self, repo: VesRepository):
        """
        Initialize the transaction for the given repository.

        Args:
            repo: The VesRepository instance to operate on
        """
        self.repo = repo
        self.index = None

    def __enter__(self) -> VesIndex:
        """
        Enter the transaction context.

        Reads the current index from disk and returns it for manipulation.

        Returns:
            The VesIndex object that can be modified during the transaction
        """
        self.index = index_read(self.repo)
        return self.index

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the transaction context.

        If no exception occurred, writes the modified index back to disk.
        If an exception occurred, the index is not written (automatic rollback).

        Args:
            exc_type: Exception type (None if no exception)
            exc_val: Exception value (None if no exception)
            exc_tb: Exception traceback (None if no exception)
        """
        if exc_type is None and self.index is not None:
            index_write(self.repo, self.index)
