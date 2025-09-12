import os
from dataclasses import dataclass
from math import ceil
from typing import List, Optional, Tuple
from src.core.repository import VesRepository, repo_file


@dataclass
class VesIndexEntry:
    """
    Represents a single entry in the Vestigium index.

    Each entry contains metadata for a file tracked by the version control system,
    including timestamps, permissions, SHA hash, and file name.
    """

    ctime: Optional[Tuple[int, int]] = None  # (timestamp in seconds, nanoseconds)
    mtime: Optional[Tuple[int, int]] = None  # (timestamp in seconds, nanoseconds)
    dev: Optional[int] = None  # Device ID containing this file
    ino: Optional[int] = None  # File's inode number
    mode_type: Optional[int] = (
        None  # Object type: b1000 (regular), b1010 (symlink), b1110 (gitlink)
    )
    mode_perms: Optional[int] = None  # Object permissions
    uid: Optional[int] = None  # User ID of owner
    gid: Optional[int] = None  # Group ID of owner
    fsize: Optional[int] = None  # Size of this object, in bytes
    sha: Optional[str] = None  # The object's SHA
    flag_assume_valid: Optional[bool] = None  # Assume valid flag
    flag_stage: Optional[int] = None  # Stage flag
    name: Optional[str] = None  # Name of the object (full path)


@dataclass
class VesIndex:
    """
    Represents the Vestigium index containing all tracked file entries.

    The index is the main data structure that maintains the state of files in the
    working directory and is used to prepare commits.

    Attributes:
        version: Version of the index format (usually 2)
        entries: List of VesIndexEntry representing tracked files
    """

    version: int = 2
    entries: Optional[List[VesIndexEntry]] = None

    def __post_init__(self):
        """Initialize the entries list if not provided."""
        if self.entries is None:
            self.entries = []


def index_read(repo: VesRepository) -> Optional[VesIndex]:
    """
    Read the repository index file and return a VesIndex object.

    This method reads the binary index file from the repository and parses it
    to create a VesIndex object containing all tracked file entries.
    If the index file doesn't exist (new repository), returns an empty VesIndex.

    Args:
        repo: The VesRepository instance to read the index from

    Returns:
        A VesIndex object containing entries read from the file, or None
        if the index file cannot be found or read

    Raises:
        AssertionError: If the file signature is invalid or the version
                       is not supported
    """
    index_file = repo_file(repo, "index")

    # New repositories have no index!
    if index_file is None or not os.path.exists(index_file):
        return VesIndex()

    with open(index_file, "rb") as f:
        raw = f.read()

    header = raw[:12]
    signature = header[:4]
    assert signature == b"DIRC"  # Stands for "DirCache"
    version = int.from_bytes(header[4:8], "big")
    assert version == 2, "ves only supports index file version 2"
    count = int.from_bytes(header[8:12], "big")

    entries = list()

    content = raw[12:]
    idx = 0
    for _ in range(count):
        # Read creation time, as a unix timestamp (seconds since
        # 1970-01-01 00:00:00, the "epoch")
        ctime_s = int.from_bytes(content[idx : idx + 4], "big")
        # Read creation time, as nanoseconds after that timestamps,
        # for extra precision.
        ctime_ns = int.from_bytes(content[idx + 4 : idx + 8], "big")
        # Same for modification time: first seconds from epoch.
        mtime_s = int.from_bytes(content[idx + 8 : idx + 12], "big")
        # Then extra nanoseconds
        mtime_ns = int.from_bytes(content[idx + 12 : idx + 16], "big")
        # Device ID
        dev = int.from_bytes(content[idx + 16 : idx + 20], "big")
        # Inode
        ino = int.from_bytes(content[idx + 20 : idx + 24], "big")
        # Ignored.
        unused = int.from_bytes(content[idx + 24 : idx + 26], "big")
        assert 0 == unused
        mode = int.from_bytes(content[idx + 26 : idx + 28], "big")
        mode_type = mode >> 12
        assert mode_type in [0b1000, 0b1010, 0b1110]
        mode_perms = mode & 0b0000000111111111
        # User ID
        uid = int.from_bytes(content[idx + 28 : idx + 32], "big")
        # Group ID
        gid = int.from_bytes(content[idx + 32 : idx + 36], "big")
        # Size
        fsize = int.from_bytes(content[idx + 36 : idx + 40], "big")
        # SHA (object ID).  We'll store it as a lowercase hex string
        # for consistency.
        sha = format(int.from_bytes(content[idx + 40 : idx + 60], "big"), "040x")
        # Flags we're going to ignore
        flags = int.from_bytes(content[idx + 60 : idx + 62], "big")
        # Parse flags
        flag_assume_valid = (flags & 0b1000000000000000) != 0
        flag_extended = (flags & 0b0100000000000000) != 0
        assert not flag_extended
        flag_stage = flags & 0b0011000000000000
        # Length of the name.  This is stored on 12 bits, some max
        # value is 0xFFF, 4095.  Since names can occasionally go
        # beyond that length, git treats 0xFFF as meaning at least
        # 0xFFF, and looks for the final 0x00 to find the end of the
        # name --- at a small, and probably very rare, performance
        # cost.
        name_length = flags & 0b0000111111111111

        # We've read 62 bytes so far.
        idx += 62

        if name_length < 0xFFF:
            assert content[idx + name_length] == 0x00
            raw_name = content[idx : idx + name_length]
            idx += name_length + 1
        else:
            print(f"Notice: Name is 0x{name_length:X} bytes long.")
            # This probably wasn't tested enough.  It works with a
            # path of exactly 0xFFF bytes.  Any extra bytes broke
            # something between git, my shell and my filesystem.
            null_idx = content.find(b"\x00", idx + 0xFFF)
            raw_name = content[idx:null_idx]
            idx = null_idx + 1

        # Just parse the name as utf8.
        name = raw_name.decode("utf8")

        # Data is padded on multiples of eight bytes for pointer
        # alignment, so we skip as many bytes as we need for the next
        # read to start at the right position.

        idx = 8 * ceil(idx / 8)

        # And we add this entry to our list.
        entries.append(
            VesIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=dev,
                ino=ino,
                mode_type=mode_type,
                mode_perms=mode_perms,
                uid=uid,
                gid=gid,
                fsize=fsize,
                sha=sha,
                flag_assume_valid=flag_assume_valid,
                flag_stage=flag_stage,
                name=name,
            )
        )

    return VesIndex(version=version, entries=entries)
