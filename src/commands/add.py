from argparse import Namespace
from src.core.repository import repo_find
import os
from src.core.index import index_read, index_write
from src.core.repository import VesRepository
from src.core.objects import object_hash
from src.core.index import VesIndexEntry
from src.commands.rm import rm


def cmd_add(args: Namespace) -> None:
    """
    Command line interface for adding files to the Vestigium repository.

    This function serves as the entry point for the 'ves add' command. It locates
    the repository and delegates the actual addition operation to the add() function.

    Args:
        args: Parsed command line arguments containing the paths to add

    Note:
        If no repository is found in the current directory or its parents,
        the function returns silently without performing any operation.
    """
    repo = repo_find()
    assert repo is not None
    add(repo, args.path)


def add(
    repo: VesRepository,
    paths: list[str],
    delete: bool = True,
    skip_missing: bool = False,
) -> None:
    """
    Add files to the Vestigium index (staging area).

    This function stages files for the next commit by adding them to the repository index.
    It reads file content, computes SHA hashes, collects filesystem metadata, and creates
    index entries. Files are first removed from the index (if present) to ensure clean updates.

    The staging process:
    1. Remove existing entries for the specified paths (without deleting files)
    2. Validate that all paths exist and are within the repository worktree
    3. Compute SHA hash of file content and store as blob object
    4. Collect filesystem metadata (timestamps, permissions, size, etc.)
    5. Create new index entries with all metadata
    6. Write updated index to disk

    Args:
        repo: The VesRepository instance to operate on
        paths: List of file paths to add (can be relative or absolute)
        delete: Unused parameter, kept for interface compatibility
        skip_missing: Unused parameter, kept for interface compatibility

    Raises:
        Exception: If any path is not a file or is outside the repository worktree
        OSError: If file cannot be read or filesystem metadata cannot be accessed

    Note:
        Files must exist and be regular files (not directories or symlinks).
        The function automatically converts paths to be relative to the repository root.
    """
    # Remove existing entries without deleting files
    rm(repo, paths, delete=False, skip_missing=True)

    worktree = repo.worktree + os.sep

    # Validate paths and convert to (absolute, relative) pairs
    clean_paths = set()
    for path in paths:
        abspath = os.path.abspath(path)
        if not (abspath.startswith(worktree) and os.path.isfile(abspath)):
            raise Exception(f"Not a file, or outside the worktree: {paths}")
        relpath = os.path.relpath(abspath, repo.worktree)
        clean_paths.add((abspath, relpath))

    # Find and read the index.  It was modified by rm.  (This isn't
    # optimal, good enough for ves!)
    #
    # @FIXME, though: we could just move the index through
    # commands instead of reading and writing it over again.
    index = index_read(repo)

    # Process each file: compute hash and create index entry
    for abspath, relpath in clean_paths:
        with open(abspath, "rb") as fd:
            sha = object_hash(fd, b"blob", repo)

            stat = os.stat(abspath)

            # Extract timestamps with nanosecond precision
            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = VesIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=0b1000,  # Regular file
                mode_perms=0o644,  # Standard file permissions
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                flag_assume_valid=False,
                flag_stage=0,
                name=relpath,
            )
            index.entries.append(entry)

    index_write(repo, index)
