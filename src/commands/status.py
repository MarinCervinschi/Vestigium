from typing import Any, Union

from src.core.index import index_read
from src.core.objects import object_find
from src.core.repository import VesRepository, repo_file, repo_find
from src.utils.status import cmd_status_head_index, cmd_status_index_worktree


def cmd_status(_) -> None:
    """
    Display the status of the repository.

    This command shows information about the current branch, differences between
    HEAD and index, and differences between index and working tree. It provides
    a comprehensive overview of the repository state similar to 'git status'.

    Returns:
        None
    """
    repo = repo_find()
    if repo is None:
        return
    index = index_read(repo)

    cmd_status_branch(repo)
    cmd_status_head_index(repo, index)
    print()
    cmd_status_index_worktree(repo, index)


def branch_get_active(repo: VesRepository) -> Union[str, bool]:
    """
    Get the name of the currently active branch.

    This function reads the HEAD file to determine if the repository is on
    a named branch or in a detached HEAD state. It parses the HEAD reference
    to extract the branch name.

    Args:
        repo: The VesRepository instance to check

    Returns:
        The name of the active branch as a string, or False if in detached
        HEAD state or if the HEAD file cannot be read
    """
    file = repo_file(repo, "HEAD")
    if file is None:
        return False
    with open(file, "r") as f:
        head = f.read()

    if head.startswith("ref: refs/heads/"):
        return head[16:-1]
    else:
        return False


def cmd_status_branch(repo: VesRepository) -> None:
    """
    Display the current branch status.

    This function prints information about the current state of the repository:
    either the name of the active branch if on a branch, or indicates that
    HEAD is detached and shows the commit hash it points to.

    Args:
        repo: The VesRepository instance to check

    Returns:
        None
    """
    branch = branch_get_active(repo)
    if branch:
        print(f"On branch {branch}.")
    else:
        print(f"HEAD detached at {object_find(repo, 'HEAD')}")
