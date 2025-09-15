import os
from typing import Optional

from src.core.index import VesIndex
from src.core.objects import object_hash
from src.core.repository import VesRepository
from src.utils.ignore import VesIgnore, check_ignore, vesignore_read
from src.utils.tree import tree_to_dict


def cmd_status_head_index(repo: VesRepository, index: VesIndex) -> None:
    """
    Display changes between HEAD and the index (staged changes).

    This function compares the current HEAD commit with the index to show
    what changes are staged for commit. It identifies:
    - Modified files (files that exist in both HEAD and index but with different content)
    - Added files (files that exist in index but not in HEAD)
    - Deleted files (files that exist in HEAD but not in index)

    Args:
        repo: The VesRepository instance to work with
        index: The current index state

    Returns:
        None
    """
    print("Changes to be committed:")

    head = tree_to_dict(repo, "HEAD")

    for entry in index.entries:
        if entry.name in head:
            if head[entry.name] != entry.sha:
                print("  modified:", entry.name)
            del head[entry.name]  # Delete the key
        else:
            print("  added:   ", entry.name)

    # Keys still in HEAD are files that we haven't met in the index,
    # and thus have been deleted.
    for file_path in head.keys():
        print("  deleted: ", file_path)


def cmd_status_index_worktree(repo: VesRepository, index: VesIndex) -> None:
    """
    Display changes between the index and the working tree (unstaged changes).

    This function compares the index with the current working tree to show:
    - Modified files (files that exist in both index and worktree but with different content)
    - Deleted files (files that exist in index but not in worktree)
    - Untracked files (files that exist in worktree but not in index and are not ignored)

    The function performs filesystem traversal and file content comparison using
    SHA hashes to detect changes. It respects ignore rules when listing untracked files.

    Args:
        repo: The VesRepository instance to work with
        index: The current index state, can be None for new repositories

    Returns:
        None
    """
    print("Changes not staged for commit:")

    ignore = vesignore_read(repo)
    assert isinstance(ignore, VesIgnore)

    vesdir_prefix = repo.vesdir + os.path.sep

    all_files = list()

    # We begin by walking the filesystem
    for root, _, files in os.walk(repo.worktree, True):
        if root == repo.vesdir or root.startswith(vesdir_prefix):
            continue
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo.worktree)
            all_files.append(rel_path)

    # We now traverse the index, and compare real files with the cached
    # versions.

    for entry in index.entries:
        full_path = os.path.join(repo.worktree, entry.name)

        # That file *name* is in the index

        if not os.path.exists(full_path):
            print("  deleted: ", entry.name)
        else:
            stat = os.stat(full_path)

            # Compare metadata
            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]
            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):
                # If different, deep compare.
                if os.path.islink(full_path):
                    link_target = os.readlink(full_path)
                    import io

                    new_sha = object_hash(
                        io.BytesIO(link_target.encode()), b"blob", None
                    )
                else:
                    with open(full_path, "rb") as fd:
                        new_sha = object_hash(fd, b"blob", None)

                # If the hashes are the same, the files are actually the same.
                same = entry.sha == new_sha

                if not same:
                    print("  modified:", entry.name)

        if entry.name in all_files:
            all_files.remove(entry.name)

    print()
    print("Untracked files:")

    for f in all_files:
        # @TODO If a full directory is untracked, we should display
        # its name without its contents.
        if not check_ignore(ignore, f):
            print(" ", f)
