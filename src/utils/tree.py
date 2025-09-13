import os
from typing import TYPE_CHECKING

from src.core.repository import VesRepository

if TYPE_CHECKING:
    from src.core.objects import VesBlob, VesTree
    from src.core.index import VesIndexEntry, VesIndex


class VesTreeLeaf(object):
    """
    Represents a single entry in a Ves tree object.

    A tree leaf contains the metadata for a file or subdirectory within a tree,
    including its permissions, name, and SHA hash reference.

    Attributes:
        mode (bytes): File mode/permissions (e.g., b'100644' for regular files,
                     b'040000' for directories)
        path (str): Name of the file or directory
        sha (str): SHA-1 hash of the referenced object (40 hex characters)
    """

    def __init__(self, mode: bytes, path: str, sha: str) -> None:
        self.mode = mode
        self.path = path
        self.sha = sha


def tree_parse_one(raw: bytes, start: int = 0) -> tuple[int, VesTreeLeaf]:
    """
    Parse a single entry from a Ves tree object's binary data.

    Tree entries in Ves have the format: {mode} {path}\0{20-byte-sha}
    where mode is 5-6 digits, path is UTF-8 encoded, and sha is 20 raw bytes.

    Args:
        raw (bytes): Raw binary data of the tree object
        start (int): Starting position in the raw data (default: 0)

    Returns:
        tuple[int, VesTreeLeaf]: A tuple containing:
            - int: Next position to parse from (after this entry)
            - VesTreeLeaf: Parsed tree entry with mode, path, and SHA

    Raises:
        AssertionError: If mode length is not 5 or 6 digits
    """
    space_terminator = raw.find(b" ", start)
    assert space_terminator - start == 5 or space_terminator - start == 6

    mode = raw[start:space_terminator]
    if len(mode) == 5:
        # Normalize to six bytes (Ves internally uses 6 digits)
        mode = b"0" + mode

    null_terminator = raw.find(b"\x00", space_terminator)
    path = raw[space_terminator + 1 : null_terminator]

    # Extract 20-byte SHA and convert to hex string
    raw_sha = int.from_bytes(raw[null_terminator + 1 : null_terminator + 21], "big")
    sha = format(raw_sha, "040x")

    return null_terminator + 21, VesTreeLeaf(mode, path.decode("utf8"), sha)


def tree_parse(raw: bytes) -> list[VesTreeLeaf]:
    """
    Parse a complete Ves tree object from binary data.

    A tree object contains multiple entries, each representing a file or
    subdirectory. This function parses all entries sequentially until
    the end of the data is reached.

    Args:
        raw (bytes): Complete raw binary data of the tree object

    Returns:
        list[VesTreeLeaf]: List of parsed tree entries, each containing
                          mode, path, and SHA information

    Note:
        Tree entries are sorted by Ves in a specific order for consistency.
        This function preserves the original order from the binary data.
    """
    pos = 0
    max = len(raw)
    ret = list()

    while pos < max:
        pos, data = tree_parse_one(raw, pos)
        ret.append(data)

    return ret


def tree_leaf_sort_key(leaf: VesTreeLeaf) -> str:
    """
    Generate a sorting key for a VesTreeLeaf.
    """
    if leaf.mode.startswith(b"10"):
        return leaf.path
    else:
        return leaf.path + "/"


def tree_serialize(obj):
    obj.items.sort(key=tree_leaf_sort_key)
    ret = b""
    for i in obj.items:
        ret += i.mode
        ret += b" "
        ret += i.path.encode("utf8")
        ret += b"\x00"
        sha = int(i.sha, 16)
        ret += sha.to_bytes(20, byteorder="big")
    return ret


def tree_checkout(repo: VesRepository, tree: "VesTree", path: str) -> None:
    """
    Recursively checks out the contents of a VesTree object to the specified filesystem path.
    For each item in the tree:
    - If the item is a tree, creates a corresponding directory and recursively checks out its contents.
    - If the item is a blob, writes its data to a file at the destination path.
    - Raises an exception if an object cannot be read.
    Args:
        repo (VesRepository): The repository from which to read objects.
        tree (VesTree): The tree object representing the directory structure to check out.
        path (str): The filesystem path where the tree should be checked out.
    Raises:
        Exception: If an object cannot be read from the repository.
    """
    from src.core.objects import object_read

    for item in tree.items:
        obj = object_read(repo, item.sha)
        if obj is None:
            raise Exception(f"Failed to read object {item.sha}")
        dest = os.path.join(path, item.path)

        if obj.fmt == b"tree":
            assert isinstance(obj, "VesTree")
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b"blob":
            assert isinstance(obj, "VesBlob")
            # @TODO Support symlinks (identified by mode 12****)
            with open(dest, "wb") as f:
                f.write(obj.blobdata)


def tree_to_dict(repo: VesRepository, ref: str, prefix: str = "") -> dict[str, str]:
    """
    Convert a tree object to a dictionary mapping file paths to SHA hashes.

    This function recursively traverses a tree object and builds a flat dictionary
    where keys are file paths (relative to the tree root) and values are the
    corresponding SHA hashes of the file contents (blobs).

    Subdirectories (trees) are recursively processed to include all nested files
    in the resulting dictionary. The function handles the prefix path to maintain
    the correct relative paths in nested calls.

    Args:
        repo: The VesRepository instance to read objects from
        ref: Reference to the tree object (SHA hash, branch name, or tag)
        prefix: Path prefix for nested calls (used internally for recursion)

    Returns:
        A dictionary mapping file paths to their SHA hashes. Returns empty
        dictionary if the reference cannot be found or read.

    Note:
        This function is useful for comparing tree states, as it flattens
        the hierarchical tree structure into a simple path->hash mapping.
    """
    from src.core.objects import object_find, object_read

    ret = dict()
    tree_sha = object_find(repo, ref, fmt=b"tree")
    if tree_sha is None:
        return ret
    tree = object_read(repo, tree_sha)
    if tree is None:
        return ret

    assert isinstance(tree, "VesTree")
    for leaf in tree.items:
        full_path = os.path.join(prefix, leaf.path)

        # We read the object to extract its type (this is uselessly
        # expensive: we could just open it as a file and read the
        # first few bytes)
        is_subtree = leaf.mode.startswith(b"04")

        # Depending on the type, we either store the path (if it's a
        # blob, so a regular file), or recurse (if it's another tree,
        # so a subdir)
        if is_subtree:
            ret.update(tree_to_dict(repo, leaf.sha, full_path))
        else:
            ret[full_path] = leaf.sha
    return ret


def tree_from_index(repo: VesRepository, index: VesIndex) -> str:
    """
    Create a tree object from the current index state.

    This function converts the index (staging area) into a hierarchical tree structure
    suitable for creating commits. It processes all index entries, organizes them by
    directory structure, and creates tree objects for each directory level.

    The algorithm works bottom-up:
    1. Groups index entries by their directory paths
    2. Creates all directory entries up to the root
    3. Processes directories from deepest to shallowest
    4. For each directory, creates a tree object containing files and subdirectories
    5. Writes tree objects to the repository store
    6. Returns the SHA hash of the root tree

    Args:
        repo: The VesRepository instance to write tree objects to
        index: The VesIndex containing staged file entries

    Returns:
        The SHA-1 hash of the root tree object as a hex string

    Raises:
        AttributeError: If index entries contain invalid data (None names or SHAs)
        OSError: If tree objects cannot be written to the repository
        ValueError: If index has no entries or is empty

    Note:
        This function is typically called during commit creation to capture
        the current staged state as a tree structure.
    """
    from src.core.objects import object_write, VesTree

    if index.entries is None:
        raise ValueError("Index has no entries")

    contents = dict()
    contents[""] = list()

    # Group entries by directory path
    for entry in index.entries:
        if entry.name is None:
            continue  # Skip invalid entries
        dirname = os.path.dirname(entry.name)

        # Create all directory entries up to root
        key = dirname
        while key != "":
            if not key in contents:
                contents[key] = list()
            key = os.path.dirname(key)

        contents[dirname].append(entry)

    # Process directories from deepest to shallowest
    sorted_paths = sorted(contents.keys(), key=len, reverse=True)

    sha = None

    for path in sorted_paths:
        tree = VesTree()

        # Create tree entries for current directory
        for entry in contents[path]:
            if isinstance(entry, VesIndexEntry):
                # Handle regular file entry
                if entry.name is None or entry.sha is None:
                    continue  # Skip invalid entries

                leaf_mode = f"{entry.mode_type:02o}{entry.mode_perms:04o}".encode(
                    "ascii"
                )
                leaf = VesTreeLeaf(
                    mode=leaf_mode, path=os.path.basename(entry.name), sha=entry.sha
                )
            else:
                # Handle subdirectory (stored as (basename, SHA) tuple)
                leaf = VesTreeLeaf(mode=b"040000", path=entry[0], sha=entry[1])

            tree.items.append(leaf)

        # Write tree object and get its SHA
        sha = object_write(tree, repo)

        # Add tree to parent directory
        parent = os.path.dirname(path)
        base = os.path.basename(path)
        contents[parent].append((base, sha))

    if sha is None:
        raise ValueError("Failed to create tree: no entries processed")

    return sha
