import os
from argparse import Namespace
from datetime import datetime

from src.commands.status import branch_get_active
from src.core.index import index_read
from src.core.objects import VesCommit, object_find, object_write
from src.core.repository import VesRepository, repo_file, repo_find
from src.utils.config import vesconfig_read, vesconfig_user_get
from src.utils.tree import tree_from_index


def cmd_commit(args: Namespace) -> None:
    """
    Command line interface for creating commits in the Vestigium repository.

    This function serves as the entry point for the 'ves commit' command. It orchestrates
    the commit creation process by reading the current index, creating tree objects,
    building the commit object, and updating repository references.

    The commit process:
    1. Locates the repository and reads the current index
    2. Creates tree objects from staged files
    3. Creates a commit object with metadata and message
    4. Updates HEAD or the active branch reference

    Args:
        args: Parsed command line arguments containing the commit message

    Note:
        If no repository is found, the function returns silently.
        The commit message is expected to be in args.message.
    """
    repo = repo_find()
    if repo is None:
        return
    index = index_read(repo)

    tree = tree_from_index(repo, index)

    author = vesconfig_user_get(vesconfig_read())
    if author is None:
        raise Exception(
            "No user configuration found. Please set user.name and user.email."
        )

    commit = commit_create(
        repo,
        tree,
        object_find(repo, "HEAD"),
        author,
        datetime.now(),
        args.message,
    )

    active_branch = branch_get_active(repo)
    if active_branch and isinstance(active_branch, str):
        file = repo_file(repo, os.path.join("refs", "heads", active_branch))
        if file is None:
            raise Exception(f"Could not find file for branch {active_branch}!")
        with open(file, "w") as fd:
            fd.write(commit + "\n")
    else:
        file = repo_file(repo, "HEAD")
        if file is None:
            raise Exception("Could not find HEAD file!")
        with open(file, "w") as fd:
            fd.write(commit + "\n")


def commit_create(
    repo: VesRepository,
    tree: str,
    parent: str | None,
    author: str,
    timestamp: datetime,
    message: str,
) -> str:
    """
    Create a new commit object with the specified metadata and content.

    This function builds a commit object by combining tree reference, parent commit,
    author information, timestamp, and commit message. It formats the data according
    to the Ves commit object specification and writes it to the repository.

    The commit object contains:
    - Tree reference (SHA of the root tree)
    - Parent commit reference (if not the initial commit)
    - Author and committer information with timestamp and timezone
    - Commit message

    Args:
        repo: The VesRepository instance to write the commit to
        tree: SHA-1 hash of the root tree object
        parent: SHA-1 hash of the parent commit, or None for initial commit
        author: Author name and email (e.g., "John Doe <john@example.com>")
        timestamp: Commit timestamp as datetime object
        message: Commit message text

    Returns:
        The SHA-1 hash of the created commit object as a hex string

    Raises:
        OSError: If the commit object cannot be written to the repository

    Note:
        The timezone is automatically calculated from the timestamp.
        Author and committer are set to the same value.
    """
    commit = VesCommit()
    commit.kvlm[b"tree"] = tree.encode("ascii")
    if parent:
        commit.kvlm[b"parent"] = parent.encode("ascii")

    message = message.strip() + "\n"

    # Calculate timezone offset
    utc_offset = timestamp.astimezone().utcoffset()
    if utc_offset is None:
        offset = 0  # Default to UTC if timezone info is not available
    else:
        offset = int(utc_offset.total_seconds())

    hours = abs(offset) // 3600
    minutes = (abs(offset) % 3600) // 60
    tz = "{}{:02d}{:02d}".format("+" if offset >= 0 else "-", hours, minutes)

    # Format author string with timestamp and timezone
    author_line = author + timestamp.strftime(" %s ") + tz

    commit.kvlm[b"author"] = author_line.encode("utf8")
    commit.kvlm[b"committer"] = author_line.encode("utf8")
    commit.kvlm[None] = message.encode("utf8")

    return object_write(commit, repo)
