import os
from src.core.objects import VesTree, object_read, VesBlob
from src.core.repository import VesRepository


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


def tree_checkout(repo: VesRepository, tree: VesTree, path: str) -> None:
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

    for item in tree.items:
        obj = object_read(repo, item.sha)
        if obj is None:
            raise Exception(f"Failed to read object {item.sha}")
        dest = os.path.join(path, item.path)

        if obj.fmt == b"tree":
            assert isinstance(obj, VesTree)
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b"blob":
            assert isinstance(obj, VesBlob)
            # @TODO Support symlinks (identified by mode 12****)
            with open(dest, "wb") as f:
                f.write(obj.blobdata)
