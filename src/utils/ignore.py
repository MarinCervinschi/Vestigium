import os
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional, Tuple

from src.core.index import index_read
from src.core.objects import VesBlob, object_read
from src.core.repository import VesRepository


@dataclass
class VesIgnore:
    """
    Represents ignore rules for Vestigium repository.

    This class manages both absolute ignore rules (applied globally) and scoped
    ignore rules (applied to specific directories) to determine which files
    should be ignored by the version control system.

    Attributes:
        absolute: List of rule sets that apply to the entire repository
        scoped: Dictionary mapping directory paths to their specific ignore rules
    """

    absolute: List[List[Tuple[str, bool]]] = field(default_factory=list)
    scoped: Dict[str, List[Tuple[str, bool]]] = field(default_factory=dict)


def vesignore_read(repo: VesRepository) -> Optional[VesIgnore]:
    """
    Read and parse all ignore rules for the given repository.

    This function collects ignore rules from multiple sources:
    1. Local repository exclude file (.ves/info/exclude)
    2. Global user configuration (~/.config/ves/ignore)
    3. .vesignore files tracked in the repository index

    Args:
        repo: The VesRepository to read ignore rules from

    Returns:
        A VesIgnore object containing all parsed ignore rules, or None if
        the repository is invalid
    """
    ret = VesIgnore(absolute=list(), scoped=dict())

    # Read local configuration in .ves/info/exclude
    repo_file = os.path.join(repo.vesdir, "info/exclude")
    if os.path.exists(repo_file):
        with open(repo_file, "r") as f:
            ret.absolute.append(vesignore_parse(f.readlines()))

    # Global configuration
    if "XDG_CONFIG_HOME" in os.environ:
        config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        config_home = os.path.expanduser("~/.config")
    global_file = os.path.join(config_home, "ves/ignore")

    if os.path.exists(global_file):
        with open(global_file, "r") as f:
            ret.absolute.append(vesignore_parse(f.readlines()))

    # .vesignore files in the index
    index = index_read(repo)
    if index is None or index.entries is None:
        return ret

    for entry in index.entries:
        if entry.name is None or entry.sha is None:
            continue
        if entry.name == ".vesignore" or entry.name.endswith("/.vesignore"):
            dir_name = os.path.dirname(entry.name)
            contents = object_read(repo, entry.sha)

            assert isinstance(contents, VesBlob)
            lines = contents.blobdata.decode("utf8").splitlines()
            ret.scoped[dir_name] = vesignore_parse(lines)
    return ret


def parse_line(raw: str) -> Optional[Tuple[str, bool]]:
    """
    Parse a single line from an ignore file.

    This function handles the various ignore rule formats:
    - Lines starting with '#' are comments (ignored)
    - Lines starting with '!' are negation rules (exclude from ignore)
    - Lines starting with '\\' escape the next character
    - All other lines are standard ignore patterns

    Args:
        raw: A single line from an ignore file

    Returns:
        A tuple (pattern, should_ignore) where pattern is the file pattern
        and should_ignore is True for ignore rules, False for negation rules.
        Returns None for comment lines or empty lines.
    """
    raw = raw.strip()

    if not raw or raw[0] == "#":
        return None
    elif raw[0] == "!":
        return (raw[1:], False)
    elif raw[0] == "\\":
        return (raw[1:], True)
    else:
        return (raw, True)


def vesignore_parse(lines: List[str]) -> List[Tuple[str, bool]]:
    """
    Parse multiple lines from an ignore file into a list of rules.

    This function processes each line using parse_line and collects
    all valid rules into a single list, filtering out comments and empty lines.

    Args:
        lines: List of strings representing lines from an ignore file

    Returns:
        List of tuples (pattern, should_ignore) representing ignore rules
    """
    ret = list()

    for line in lines:
        parsed = parse_line(line)
        if parsed:
            ret.append(parsed)

    return ret


def check_ignore1(rules: List[Tuple[str, bool]], path: str) -> Optional[bool]:
    """
    Check if a path matches any rule in a single rule set.

    This function iterates through rules in order and returns the result
    of the last matching rule. Later rules override earlier ones.

    Args:
        rules: List of (pattern, should_ignore) tuples to check against
        path: File path to check

    Returns:
        True if the path should be ignored, False if it should be included,
        None if no rules match
    """
    result = None
    for pattern, value in rules:
        if fnmatch(path, pattern):
            result = value
    return result


def check_ignore_scoped(
    rules: Dict[str, List[Tuple[str, bool]]], path: str
) -> Optional[bool]:
    """
    Check if a path matches any scoped ignore rule.

    This function walks up the directory tree from the file's location,
    checking for ignore rules in each parent directory. The first matching
    rule found determines the result.

    Args:
        rules: Dictionary mapping directory paths to their ignore rules
        path: File path to check (relative to repository root)

    Returns:
        True if the path should be ignored, False if it should be included,
        None if no scoped rules match
    """
    parent = os.path.dirname(path)
    while True:
        if parent in rules:
            result = check_ignore1(rules[parent], path)
            if result != None:
                return result
        if parent == "":
            break
        parent = os.path.dirname(parent)
    return None


def check_ignore_absolute(rules: List[List[Tuple[str, bool]]], path: str) -> bool:
    """
    Check if a path matches any absolute ignore rule.

    This function checks the path against all absolute rule sets
    (from global config and repository exclude file). The first
    matching rule determines the result.

    Args:
        rules: List of rule sets to check against
        path: File path to check (relative to repository root)

    Returns:
        True if the path should be ignored, False otherwise
    """
    parent = os.path.dirname(path)
    for ruleset in rules:
        result = check_ignore1(ruleset, path)
        if result != None:
            return result
    return False  # This is a reasonable default at this point.


def check_ignore(rules: VesIgnore, path: str) -> bool:
    """
    Check if a path should be ignored according to all ignore rules.

    This function combines both scoped and absolute ignore rules to determine
    if a file should be ignored. Scoped rules take precedence over absolute rules.

    Args:
        rules: VesIgnore object containing all ignore rules
        path: File path to check (must be relative to repository root)

    Returns:
        True if the path should be ignored, False otherwise

    Raises:
        Exception: If the path is absolute instead of relative to repository root
    """
    if os.path.isabs(path):
        raise Exception(
            "This function requires path to be relative to the repository's root"
        )

    result = check_ignore_scoped(rules.scoped, path)
    if result != None:
        return result

    return check_ignore_absolute(rules.absolute, path)
