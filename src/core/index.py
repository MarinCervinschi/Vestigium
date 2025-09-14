import os
from dataclasses import dataclass, field
from math import ceil
from typing import List, Tuple

from src.core.repository import VesRepository, repo_file


@dataclass
class VesIndexEntry:
    """
    Represents a single entry in the Vestigium index.

    Each entry contains complete metadata for a file tracked by the version control system.
    This includes filesystem metadata, timestamps, permissions, and the SHA hash of the
    file content. The index entry format follows the Ves index specification.

    Attributes:
        ctime: Creation time as (seconds_since_epoch, nanoseconds) tuple
        mtime: Modification time as (seconds_since_epoch, nanoseconds) tuple
        dev: Device ID of the filesystem containing this file
        ino: Inode number of the file
        mode_type: File type bits - 0b1000 (regular file), 0b1010 (symlink), 0b1110 (gitlink)
        mode_perms: File permission bits (e.g., 0o644 for rw-r--r--)
        uid: User ID of the file owner
        gid: Group ID of the file owner
        fsize: Size of the file in bytes
        sha: SHA-1 hash of the file content as lowercase hex string (40 characters)
        flag_assume_valid: When True, Ves assumes the file hasn't changed
        flag_stage: Merge conflict stage (0=normal, 1=base, 2=ours, 3=theirs)
        name: Relative path of the file from repository root

    Note:
        All fields are required and must contain valid values when creating an entry.
        Use proper filesystem values for metadata.
    """

    ctime: Tuple[int, int]
    mtime: Tuple[int, int]
    dev: int
    ino: int
    mode_type: int
    mode_perms: int
    uid: int
    gid: int
    fsize: int
    sha: str
    flag_assume_valid: bool
    flag_stage: int
    name: str


@dataclass
class VesIndex:
    """
    Represents the Vestigium index containing all tracked file entries.

    The index is the primary data structure that maintains the state of files in the
    working directory and serves as the staging area for preparing commits. It contains
    metadata for all tracked files and is persisted as a binary file in .ves/index.

    The index file format is compatible with Ves's index format version 2:
    - Header: 12 bytes (signature "DIRC", version, entry count)
    - Entries: Variable-length records with file metadata and names
    - Padding: Entries are padded to 8-byte boundaries for alignment

    Attributes:
        version: Index format version (should be 2 for compatibility)
        entries: List of VesIndexEntry objects representing tracked files

    Note:
        The entries list is automatically initialized as empty list for each instance.
        Entries should be kept sorted by file path for optimal performance.
    """

    version: int = 2
    entries: List[VesIndexEntry] = field(default_factory=list)


def index_read(repo: VesRepository) -> VesIndex:
    """
    Read the repository index file and parse it into a VesIndex object.

    This function reads and parses the binary index file from the repository's .ves
    directory. The index file contains metadata for all tracked files and follows
    the Ves index format version 2 specification.

    The parsing process:
    1. Reads the 12-byte header (signature, version, entry count)
    2. Validates the "DIRC" magic signature and version 2 format
    3. Parses each entry's 62 bytes of fixed metadata plus variable-length name
    4. Handles name length encoding and null termination
    5. Applies 8-byte padding alignment between entries

    Args:
        repo: The VesRepository instance to read the index from

    Returns:
        A VesIndex object containing all parsed entries. Returns an empty
        VesIndex (with no entries) if the index file doesn't exist, which
        is normal for new repositories.

    Raises:
        AssertionError: If the file has invalid signature (not "DIRC"),
                       unsupported version (not 2), or malformed entry data
        OSError: If the index file exists but cannot be read
        UnicodeDecodeError: If entry names contain invalid UTF-8 sequences

    Note:
        New repositories without an index file will get an empty VesIndex.
        This is expected behavior and not an error condition.
    """
    index_file = repo_file(repo, "index")

    # New repositories have no index!
    if not os.path.exists(index_file):
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
        # Creation time
        ctime_s = int.from_bytes(content[idx : idx + 4], "big")
        ctime_ns = int.from_bytes(content[idx + 4 : idx + 8], "big")
        # Modification time
        mtime_s = int.from_bytes(content[idx + 8 : idx + 12], "big")
        mtime_ns = int.from_bytes(content[idx + 12 : idx + 16], "big")
        # Device and inode
        dev = int.from_bytes(content[idx + 16 : idx + 20], "big")
        ino = int.from_bytes(content[idx + 20 : idx + 24], "big")
        # Unused field
        unused = int.from_bytes(content[idx + 24 : idx + 26], "big")
        assert 0 == unused
        # File mode
        mode = int.from_bytes(content[idx + 26 : idx + 28], "big")
        mode_type = mode >> 12
        assert mode_type in [0b1000, 0b1010, 0b1110]
        mode_perms = mode & 0b0000000111111111
        # User and group IDs
        uid = int.from_bytes(content[idx + 28 : idx + 32], "big")
        gid = int.from_bytes(content[idx + 32 : idx + 36], "big")
        # File size and SHA
        fsize = int.from_bytes(content[idx + 36 : idx + 40], "big")
        sha = format(int.from_bytes(content[idx + 40 : idx + 60], "big"), "040x")
        # Parse flags
        flags = int.from_bytes(content[idx + 60 : idx + 62], "big")
        flag_assume_valid = (flags & 0b1000000000000000) != 0
        flag_extended = (flags & 0b0100000000000000) != 0
        assert not flag_extended
        flag_stage = flags & 0b0011000000000000
        name_length = flags & 0b0000111111111111

        idx += 62

        # Handle file name
        if name_length < 0xFFF:
            assert content[idx + name_length] == 0x00
            raw_name = content[idx : idx + name_length]
            idx += name_length + 1
        else:
            print(f"Notice: Name is 0x{name_length:X} bytes long.")
            null_idx = content.find(b"\x00", idx + 0xFFF)
            raw_name = content[idx:null_idx]
            idx = null_idx + 1

        name = raw_name.decode("utf8")

        # Apply 8-byte padding alignment
        idx = 8 * ceil(idx / 8)

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


def index_write(repo: VesRepository, index: VesIndex) -> None:
    """
    Write a VesIndex object to the repository's index file.

    This function serializes the index data structure to the binary index file format
    used by Vestigium. The index file contains metadata for all tracked files and is
    essential for staging operations and preparing commits.

    The index file format follows this structure:
    - Header (12 bytes): Magic signature "DIRC", version (4 bytes), entry count (4 bytes)
    - Entries: Variable-length entries for each tracked file containing:
      * Timestamps (creation and modification time)
      * File system metadata (device, inode, mode, uid, gid, size)
      * SHA hash of the file content
      * Flags and file name
      * Padding to align entries on 8-byte boundaries

    Args:
        repo: The VesRepository instance to write the index to
        index: The VesIndex object containing entries to write

    Raises:
        Exception: If the index file cannot be determined for the repository
        OSError: If the index file cannot be written

    Note:
        This function will overwrite any existing index file. All entries must
        have their required fields populated with valid values.
    """
    index_file = repo_file(repo, "index")

    with open(index_file, "wb") as f:

        # HEADER
        f.write(b"DIRC")
        f.write(index.version.to_bytes(4, "big"))
        f.write(len(index.entries).to_bytes(4, "big"))

        # ENTRIES
        idx = 0
        for e in index.entries:
            # Write timestamps
            f.write(e.ctime[0].to_bytes(4, "big"))
            f.write(e.ctime[1].to_bytes(4, "big"))
            f.write(e.mtime[0].to_bytes(4, "big"))
            f.write(e.mtime[1].to_bytes(4, "big"))
            # Write filesystem metadata
            f.write(e.dev.to_bytes(4, "big"))
            f.write(e.ino.to_bytes(4, "big"))
            f.write((0).to_bytes(2, "big"))  # unused field
            # Write file mode
            mode = (e.mode_type << 12) | e.mode_perms
            f.write(mode.to_bytes(2, "big"))
            # Write user/group IDs and file size
            f.write(e.uid.to_bytes(4, "big"))
            f.write(e.gid.to_bytes(4, "big"))
            f.write(e.fsize.to_bytes(4, "big"))
            # Write SHA hash
            f.write(int(e.sha, 16).to_bytes(20, "big"))

            # Prepare flags and name
            flag_assume_valid = 0x1 << 15 if e.flag_assume_valid else 0
            name_bytes = e.name.encode("utf8")
            bytes_len = len(name_bytes)
            name_length = 0xFFF if bytes_len >= 0xFFF else bytes_len

            # Write flags and name
            f.write((flag_assume_valid | e.flag_stage | name_length).to_bytes(2, "big"))
            f.write(name_bytes)
            f.write((0).to_bytes(1, "big"))

            # Update counter and apply padding
            idx += 62 + len(name_bytes) + 1
            if idx % 8 != 0:
                pad = 8 - (idx % 8)
                f.write((0).to_bytes(pad, "big"))
                idx += pad
