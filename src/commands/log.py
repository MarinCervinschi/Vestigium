from argparse import Namespace

from src.core.objects import VesCommit, object_find, object_read
from src.core.repository import VesRepository, repo_find


def cmd_log(args: Namespace) -> None:
    """
    Generate a commit history graph in Graphviz DOT format.

    This command creates a directed graph representation of the commit history
    starting from a specified commit. The output is in Graphviz DOT format
    which can be rendered into visual graphs showing commit relationships.

    Args:
        args (Namespace): Command line arguments containing:
                         - commit: Starting commit SHA or reference

    Output:
        Prints Graphviz DOT format to stdout with:
        - Nodes representing commits (labeled with short SHA and message)
        - Directed edges showing parent-child relationships

    Example output:
        digraph veslog{
          node[shape=rect]
          c_abc123f [label="abc123f: Initial commit"]
          c_def456a [label="def456a: Add feature"]
          c_def456a -> c_abc123f;
        }
    """
    repo = repo_find()
    assert repo is not None

    print("digraph veslog{")
    print("  node[shape=rect]")
    sha = object_find(repo, args.commit)
    if sha is None:
        return
    log_graphviz(repo, sha, set())
    print("}")


def log_graphviz(repo: VesRepository, sha: str, seen: set) -> None:
    """
    Recursively generate Graphviz nodes and edges for commit history.

    This function traverses the commit graph starting from a given commit SHA,
    following parent relationships to build a complete history graph. It uses
    a depth-first approach and maintains a seen set to avoid infinite loops
    in case of complex merge scenarios.

    Args:
        repo (VesRepository): The repository to read commits from
        sha (str): SHA-1 hash of the current commit to process
        seen (set): Set of already processed commit SHAs to avoid cycles

    Output:
        Prints Graphviz nodes and edges to stdout:
        - Node format: c_{sha} [label="{short_sha}: {commit_message}"]
        - Edge format: c_{child_sha} -> c_{parent_sha};

    Processing details:
        - Commit messages are escaped for Graphviz (backslashes and quotes)
        - Only the first line of multi-line commit messages is used
        - Handles both single parents (normal commits) and multiple parents (merges)
        - Recursively processes all parent commits
    """

    if sha in seen:
        return
    seen.add(sha)

    commit = object_read(repo, sha)
    if commit is None:
        return
    assert type(commit) == VesCommit

    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\")
    message = message.replace('"', '\\"')

    if "\n" in message:
        message = message[: message.index("\n")]

    print(f'  c_{sha} [label="{sha[0:7]}: {message}"]')
    assert commit.fmt == b"commit"

    if not b"parent" in commit.kvlm.keys():
        # Base case: initial commit has no parents
        return

    parents = commit.kvlm[b"parent"]

    if type(parents) != list:
        parents = [parents]

    for p in parents:
        p = p.decode("ascii")
        print(f"  c_{sha} -> c_{p};")
        log_graphviz(repo, p, seen)
