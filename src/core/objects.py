import hashlib
import os
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.core.repository import VesRepository, repo_file


@dataclass
class VesObject(ABC):
    """
    Abstract base class for all VCS objects (blobs, trees, commits, tags).

    This class defines the interface that all VCS objects must implement.
    Objects can be created from raw byte data (when reading from storage)
    or initialized empty (when creating new objects).
    """

    def __init__(self, data: Optional[bytes] = None) -> None:
        """
        Initialize a VCS object.

        Args:
            data (Optional[bytes]): Raw byte data to deserialize. If None,
                                  initializes an empty object.
        """
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    @abstractmethod
    def serialize(self, repo: VesRepository) -> bytes:
        """
        Serialize the object to bytes for storage.

        This method must be implemented by subclasses to convert the object's
        internal representation back to the byte format used for storage.

        Args:
            repo (VesRepository): The repository context for serialization.

        Returns:
            bytes: The serialized object data.
        """
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, data: bytes) -> None:
        """
        Deserialize bytes into the object's internal representation.

        This method must be implemented by subclasses to parse raw byte data
        from the object store and populate the object's attributes.

        Args:
            data (bytes): Raw byte data from the object store.
        """
        raise NotImplementedError

    def init(self) -> None:
        """
        Initialize an empty object.

        This method can be overridden by subclasses to set up default values
        for new objects. The default implementation does nothing.
        """
        pass


class VesCommit(VesObject):
    """
    Represents a commit object in the VCS.

    Commits store metadata about a change including author, committer,
    timestamp, commit message, and references to tree and parent commits.
    """

    def serialize(self, repo: VesRepository) -> bytes:
        """Serialize commit object to bytes."""
        # TODO: Implement commit serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into commit object."""
        # TODO: Implement commit deserialization
        pass


class VesTree(VesObject):
    """
    Represents a tree object in the VCS.

    Trees store directory listings with file/directory names, permissions,
    and SHA hashes of the contained objects.
    """

    def serialize(self, repo: VesRepository) -> bytes:
        """Serialize tree object to bytes."""
        # TODO: Implement tree serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into tree object."""
        # TODO: Implement tree deserialization
        pass


class VesTag(VesObject):
    """
    Represents a tag object in the VCS.

    Tags are lightweight references to commits, often used to mark
    specific versions or releases.
    """

    def serialize(self, repo: VesRepository) -> bytes:
        """Serialize tag object to bytes."""
        # TODO: Implement tag serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into tag object."""
        # TODO: Implement tag deserialization
        pass


class VesBlob(VesObject):
    """
    Represents a blob object in the VCS.

    Blobs store file content as raw binary data. They are the leaf nodes
    in the VCS object graph and contain no metadata about filenames or
    permissions - that information is stored in tree objects.
    """

    def serialize(self, repo: VesRepository) -> bytes:
        """Serialize blob object to bytes."""
        # TODO: Implement blob serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into blob object."""
        # TODO: Implement blob deserialization
        pass


def object_read(repo: VesRepository, sha: str) -> Optional[VesObject]:
    """
    Reads and deserializes a VCS object from the repository's object store.

    This function locates an object by its SHA hash, decompresses it using zlib,
    parses the object header to determine its type and size, and creates the
    appropriate object instance (VesBlob, VesTree, VesCommit, or VesTag).

    Object storage format:
        - Objects are stored in .ves/objects/{first_2_chars}/{remaining_chars}
        - Content is zlib-compressed
        - Format: {type} {size}\0{content}

    Args:
        repo (VesRepository): The repository to read from.
        sha (str): The SHA-1 hash of the object to read (40 hex characters).

    Returns:
        Optional[VesObject]: The deserialized object instance, or None if not found.

    Raises:
        Exception: If the object is malformed (wrong size) or has unknown type.

    Example:
        repo = repo_find()
        obj = object_read(repo, "a1b2c3d4e5f6...")
        if obj:
            print(f"Found object of type: {type(obj).__name__}")
    """
    path = repo_file(repo, "objects", sha[:2], sha[2:])

    if path is None or not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        object_type_end = raw.find(b" ")
        fmt = raw[:object_type_end]

        object_size_end = raw.find(b"\x00", object_type_end)
        size = int(raw[object_type_end:object_size_end].decode("ascii"))

        if size != len(raw) - object_size_end - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        match fmt:
            case b"commit":
                c = VesCommit
            case b"tree":
                c = VesTree
            case b"tag":
                c = VesTag
            case b"blob":
                c = VesBlob
            case _:
                raise Exception(f"Unknown type {fmt.decode('ascii')} for object {sha}")

        return c(raw[object_size_end + 1 :])
