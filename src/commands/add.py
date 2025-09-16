import os
from argparse import Namespace
from io import BytesIO

from src.core.index import VesIndexEntry
from src.core.objects import object_hash
from src.core.repository import VesRepository, repo_find
from src.core.transaction import IndexTransaction, rm_in_memory


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
    Add files to the Vestigium index (staging area) using transaction management.

    This function stages files for the next commit by adding them to the repository index.
    It uses IndexTransaction for efficient I/O operations, reading the index once at the
    beginning and writing it once at the end.

    The staging process:
    1. Remove existing entries for the specified paths (without deleting files)
    2. Validate that all paths exist and are within the repository worktree
    3. Compute SHA hash of file content and store as blob object
    4. Collect filesystem metadata (timestamps, permissions, size, etc.)
    5. Create new index entries with all metadata
    6. Transaction automatically writes updated index to disk

    Args:
        repo: The VesRepository instance to operate on
        paths: List of file paths to add (can be relative or absolute)
        delete: Unused parameter, kept for interface compatibility
        skip_missing: Unused parameter, kept for interface compatibility

    Raises:
        Exception: If any path is not a file or is outside the repository worktree
        OSError: If file cannot be read or filesystem metadata cannot be accessed

    Note:
        Files must exist and be regular files or symlinks (not directories).
        The function automatically converts paths to be relative to the repository root.
        Symlinks are stored as their target path, not the content of the target file.
    """
    with IndexTransaction(repo) as index:
        rm_in_memory(index, repo, paths, delete=False, skip_missing=True)

        clean_paths = set()
        for path in paths:
            abspath = os.path.abspath(path)
            if not (os.path.isfile(abspath) or os.path.islink(abspath)):
                raise Exception(f"Not a file or symlink: {abspath}")
            relpath = os.path.relpath(abspath, repo.worktree)
            clean_paths.add((abspath, relpath))

        for abspath, relpath in clean_paths:
            if os.path.islink(abspath):
                link_target = os.readlink(abspath)
                sha = object_hash(BytesIO(link_target.encode("utf-8")), b"blob", repo)
                stat = os.lstat(
                    abspath
                )  # Use lstat to get symlink metadata, not target
                mode_type = 0b1010  # Symlink mode (120000 in octal)
                mode_perms = 0o000  # Symlinks don't have traditional permissions
            else:
                with open(abspath, "rb") as fd:
                    sha = object_hash(fd, b"blob", repo)
                stat = os.stat(abspath)
                mode_type = 0b1000  # Regular file
                mode_perms = 0o644  # Standard file permissions

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = VesIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=mode_type,
                mode_perms=mode_perms,
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                flag_assume_valid=False,
                flag_stage=0,
                name=relpath,
            )

            index.entries.append(entry)