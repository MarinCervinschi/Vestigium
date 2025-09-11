import configparser
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VesRepository:
    """A ves repository."""

    _worktree: str
    _vesdir: str = field(init=False)
    _conf: configparser.ConfigParser = field(init=False)

    def __init__(self, path: str, force: bool = False) -> None:
        self._worktree = path
        self._vesdir = os.path.join(path, ".ves")

        if not (force or os.path.isdir(self._vesdir)):
            raise Exception(f"Not a Ves repository {path}")

        self._conf = configparser.ConfigParser()
        cf: Optional[str] = repo_file(self, "config")
        if cf and os.path.exists(cf):
            self._conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers: int = int(self._conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion: {vers}")

    @property
    def worktree(self) -> str:
        return self._worktree

    @property
    def vesdir(self) -> str:
        return self._vesdir

    @property
    def conf(self) -> configparser.ConfigParser:
        return self._conf


def repo_path(repo: VesRepository, *path: str) -> str:
    """
    Returns the absolute path under the repository's .ves directory, joining all given path components.
    Example: repo_path(repo, "objects", "abc") → /path/to/repo/.ves/objects/abc
    Args:
        repo: VesRepository instance.
        *path: Path components to join under .ves.
    Returns:
        str: The resulting absolute path.
    """
    return os.path.join(repo.vesdir, *path)


def repo_file(repo: VesRepository, *path: str, mkdir: bool = False) -> Optional[str]:
    """
    Returns the absolute path to a file under the repository's .ves directory, optionally creating parent directories.
    Example: repo_file(repo, "refs", "remotes", "origin", "HEAD") will create .ves/refs/remotes/origin if mkdir=True.
    Args:
        repo: VesRepository instance.
        *path: Path components for the file.
        mkdir: If True, create parent directories if they do not exist.
    Returns:
        Optional[str]: The absolute file path, or None if creation failed.
    """
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)
    return None


def repo_dir(repo: VesRepository, *path: str, mkdir: bool = False) -> Optional[str]:
    """
    Returns the absolute path to a directory under the repository's .ves directory, optionally creating it.
    Example: repo_dir(repo, "objects", mkdir=True) will create .ves/objects if it does not exist.
    Args:
        repo: VesRepository instance.
        *path: Path components for the directory.
        mkdir: If True, create the directory if it does not exist.
    Returns:
        Optional[str]: The absolute directory path, or None if not created/found.
    Raises:
        Exception: If the path exists but is not a directory.
    """
    dir_path = repo_path(repo, *path)
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            return dir_path
        else:
            raise Exception(f"Not a directory {dir_path}")
    if mkdir:
        os.makedirs(dir_path)
        return dir_path
    else:
        return None


def repo_create(path: str) -> VesRepository:
    """
    Creates a new VesRepository at the given path, initializing all required directories and files.
    This includes .ves/branches, .ves/objects, .ves/refs/tags, .ves/refs/heads, and default files like description, HEAD, and config.
    Args:
        path: The root path where the repository will be created.
    Returns:
        VesRepository: The initialized repository object.
    Raises:
        Exception: If the path is not a directory or is not empty.
    """
    repo = VesRepository(path, True)

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory!")
        if os.path.exists(repo.vesdir) and os.listdir(repo.vesdir):
            raise Exception(f"{path} is not empty!")
    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    description_path = repo_file(repo, "description")
    if not description_path:
        raise Exception("Could not create description file path.")
    with open(description_path, "w") as f:
        f.write(
            "Unnamed repository; edit this file 'description' to name the repository.\n"
        )

    head_path = repo_file(repo, "HEAD")
    if not head_path:
        raise Exception("Could not create HEAD file path.")
    with open(head_path, "w") as f:
        f.write("ref: refs/heads/master\n")

    config_path = repo_file(repo, "config")
    if not config_path:
        raise Exception("Could not create config file path.")
    with open(config_path, "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo


def repo_default_config() -> configparser.ConfigParser:
    """
    Returns a default configuration for a VesRepository, with core settings.
    The config includes repositoryformatversion, filemode, and bare options.
    Returns:
        configparser.ConfigParser: The default configuration object.
    """
    ret = configparser.ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")
    return ret


def repo_find(path: str = ".", required: bool = True) -> Optional[VesRepository]:
    """
    Finds a VesRepository by searching upward through the directory tree starting from the given path.

    Args:
        path (str): The starting path to search from. Defaults to current directory (".").
        required (bool): If True, raises an exception when no repository is found.
                        If False, returns None when no repository is found.

    Returns:
        Optional[VesRepository]: The VesRepository object if found, None if not found and required=False.

    Raises:
        Exception: If no repository is found and required=True.
    """

    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".ves")):
        return VesRepository(path)

    parent = os.path.realpath(os.path.join(path, ".."))
    if parent == path:
        if required:
            raise Exception("No ves directory.")
        else:
            return None

    return repo_find(parent, required)
