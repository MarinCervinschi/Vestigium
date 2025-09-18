import hashlib
import os
import re
import zlib
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from typing import IO, Any, Dict, List, Optional

from src.core.refs import ref_resolve
from src.core.repository import VesRepository, repo_dir, repo_file
from src.utils.kvlm import kvlm_parse, kvlm_serialize
from src.utils.tree import VesTreeLeaf, tree_parse, tree_serialize


@dataclass(kw_only=True, slots=True)
class VesObject(ABC):
    """
    Abstract base class for all VCS objects (blobs, trees, commits, tags).

    This class defines the interface that all VCS objects must implement.
    Objects can be created from raw byte data (when reading from storage)
    or initialized empty (when creating new objects).
    """

    data: InitVar[Optional[bytes]] = None

    def __post_init__(self, data: Optional[bytes]) -> None:
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

    @property
    @abstractmethod
    def format_type(self) -> bytes:
        """Object format type identifier."""
        pass

    @abstractmethod
    def serialize(self, repo: Optional[VesRepository] = None) -> bytes:
        """
        Serialize the object to bytes for storage.

        Args:
            repo (Optional[VcsRepository]): The repository context for serialization.

        Returns:
            bytes: The serialized object data.
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> None:
        """
        Deserialize bytes into the object's internal representation.

        Args:
            data (bytes): Raw byte data from the object store.
        """
        pass

    def init(self) -> None:
        """
        Initialize an empty object.

        This method can be overridden by subclasses to set up default values
        for new objects. The default implementation does nothing.
        """
        pass


@dataclass(kw_only=True, slots=True)
class VesCommit(VesObject):
    """
    Represents a commit object in the VCS.

    Attributes:
        kvlm (dict): Dictionary containing commit metadata.
    """

    kvlm: Dict[Optional[bytes], Any] = field(default_factory=dict)

    @property
    def format_type(self) -> bytes:
        return b"commit"

    def serialize(self, repo: Optional[VesRepository] = None) -> bytes:
        """Serialize commit object to bytes in KVLM format."""
        return kvlm_serialize(self.kvlm)

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into commit object."""
        self.kvlm = kvlm_parse(data)

    def init(self) -> None:
        """Initialize an empty commit object with empty KVLM dictionary."""
        self.kvlm = dict()


@dataclass(kw_only=True, slots=True)
class VesTree(VesObject):
    """Represents a tree object in the VCS."""

    items: List[VesTreeLeaf] = field(default_factory=list)

    @property
    def format_type(self) -> bytes:
        return b"tree"

    def serialize(self, repo: Optional[VesRepository] = None) -> bytes:
        """Serialize tree object to bytes."""
        return tree_serialize(self)

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into tree object."""
        self.items = tree_parse(data)

    def init(self) -> None:
        self.items = list()


@dataclass(kw_only=True, slots=True)
class VesBlob(VesObject):
    """Represents a blob object in the VCS."""

    blobdata: bytes = b""

    @property
    def format_type(self) -> bytes:
        return b"blob"

    def serialize(self, repo: Optional[VesRepository] = None) -> bytes:
        """Serialize blob object to bytes."""
        return self.blobdata

    def deserialize(self, data: bytes) -> None:
        """Deserialize bytes into blob object."""
        self.blobdata = data


@dataclass(kw_only=True, slots=True)
class VesTag(VesCommit):
    """Represents a tag object in the VCS."""

    @property
    def format_type(self) -> bytes:
        return b"tag"


def _object_read_raw(repo: VesRepository, sha: str) -> Optional[tuple[bytes, bytes]]:
    """
    Reads the raw data of a VCS object from the repository's object store.

    Returns:
        Optional[tuple[bytes, bytes]]: A tuple of (object_type, content_data)
                                       or None if not found.
    """
    path = repo_file(repo, "objects", sha[:2], sha[2:])

    if not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        object_type_end = raw.find(b" ")
        if object_type_end == -1:
            raise Exception(f"Malformed object {sha}: no space separator")

        fmt = raw[:object_type_end]

        object_size_end = raw.find(b"\x00", object_type_end)
        if object_size_end == -1:
            raise Exception(f"Malformed object {sha}: no null separator")

        size = int(raw[object_type_end:object_size_end].decode("ascii"))
        if size != len(raw) - object_size_end - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        content = raw[object_size_end + 1 :]
        return (fmt, content)


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

    """
    result = _object_read_raw(repo, sha)
    if result is None:
        return None

    fmt, content = result

    match fmt:
        case b"commit":
            c: type[VesObject] = VesCommit
        case b"tree":
            c = VesTree
        case b"tag":
            c = VesTag
        case b"blob":
            c = VesBlob
        case _:
            raise Exception(f"Unknown type {fmt.decode('ascii')} for object {sha}")

    return c(data=content)


def object_write(obj: VesObject, repo: Optional[VesRepository] = None) -> str:
    """
    Writes and compresses a VCS object to the repository's object store.

    This function serializes a VCS object, calculates its SHA-1 hash, and stores
    it in the repository's object store if provided. The object is compressed
    using zlib before storage.

    Object storage format:
        - Objects are stored in .ves/objects/{first_2_chars}/{remaining_chars}
        - Content is zlib-compressed
        - Format: {type} {size}\0{content}

    Args:
        obj (VesObject): The VCS object to write (VesBlob, VesTree, VesCommit, or VesTag).
        repo (Optional[VesRepository]): The repository to write to. If None,
                                      only calculates the SHA without storing.

    Returns:
        str: The SHA-1 hash of the object (40 hex characters).
    """
    data = obj.serialize()

    # Create the object format: {type} {size}\0{content}
    result = obj.format_type + b" " + str(len(data)).encode() + b"\x00" + data
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        path = repo_file(repo, "objects", sha[:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(zlib.compress(result))
    return sha


def object_find(
    repo: VesRepository, name: str, fmt: Optional[bytes] = None, follow: bool = True
) -> Optional[str]:
    """
    Finds a VCS object by its name (SHA-1 hash or filename) in the repository.

    Args:
        repo (VesRepository): The repository to search in.
        name (str): The name (SHA-1 hash or filename) of the object to find.
        fmt (Optional[bytes]): The expected format of the object (e.g., b"blob").
        follow (bool): Whether to follow symlinks (if any) to find the object.

    Returns:
        Optional[str]: The SHA-1 hash of the found object, or None if not found.
    """
    sha_list = object_resolve(repo, name)

    if not sha_list:
        raise Exception(f"No such reference {name}.")

    if len(sha_list) > 1:
        candidates = [s for s in sha_list if s is not None]
        raise Exception(
            f"Ambiguous reference {name}: Candidates are:\n - {'\n - '.join(candidates)}."
        )

    sha = sha_list[0]
    if sha is None:
        return None

    if not fmt:
        return sha

    while True:
        header_result = _object_read_raw(repo, sha)
        if header_result is None:
            raise Exception(f"Cannot read object {sha}.")

        obj_type = header_result[0]

        if obj_type == fmt:
            return sha

        if not follow:
            return None

        # Follow tags - now we need the full object to get the reference
        if obj_type == b"tag":
            obj = object_read(repo, sha)
            assert isinstance(obj, VesTag)
            sha = obj.kvlm[b"object"].decode("ascii")
        elif obj_type == b"commit" and fmt == b"tree":
            obj = object_read(repo, sha)
            assert isinstance(obj, VesCommit)
            sha = obj.kvlm[b"tree"].decode("ascii")
        else:
            return None


def object_hash(fd: IO[bytes], fmt: bytes, repo: Optional[VesRepository] = None) -> str:
    """
    Computes the hash of a version control object from a file-like input and writes it to the repository if provided.

    Args:
        fd (IO[bytes]): A file-like object opened in binary mode containing the object data.
        fmt (bytes): The type of the object, must be one of b"commit", b"tree", b"tag", or b"blob".
        repo (Optional[VesRepository], optional): The repository to write the object to. Defaults to None.

    Returns:
        str: The hash of the object.

    Raises:
        Exception: If an unknown object type is provided in fmt.
    """
    data = fd.read()

    match fmt:
        case b"commit":
            obj: VesObject = VesCommit(data=data)
        case b"tree":
            obj = VesTree(data=data)
        case b"tag":
            obj = VesTag(data=data)
        case b"blob":
            obj = VesBlob(data=data)
        case _:
            raise Exception(f"Unknown type {fmt.decode('utf-8')}!")

    return object_write(obj, repo)


def object_resolve(repo: VesRepository, name: str) -> Optional[List[Optional[str]]]:
    """
    Resolve a name to one or more object SHA hashes in the repository.

    This function implements Ves's flexible object resolution strategy, supporting
    multiple naming conventions and returning all possible matches. It's designed
    to handle ambiguous references gracefully by returning a list of candidates.

    Args:
        repo (VesRepository): The repository to search in
        name (str): The name to resolve, which can be:
                   - "HEAD": Special literal for current commit
                   - Full SHA hash (40 hex characters)
                   - Partial SHA hash (4-39 hex characters)
                   - Tag name (resolves to refs/tags/{name})
                   - Branch name (resolves to refs/heads/{name})
                   - Remote branch name (resolves to refs/remotes/{name})

    Returns:
        Optional[List[Optional[str]]]: List of matching SHA hashes, or None if:
                                      - Empty/whitespace-only name provided
                                      - No matches found

    Resolution priority and behavior:
        1. HEAD literal: Returns the SHA that HEAD points to
        2. SHA hash patterns: Searches object store for matching hashes
           - Supports partial hashes (minimum 4 characters)
           - Case-insensitive matching
        3. Tag references: Looks for refs/tags/{name}
        4. Branch references: Looks for refs/heads/{name}
        5. Remote branches: Looks for refs/remotes/{name}

    Multiple matches can occur with:
        - Partial SHA hashes that match multiple objects
        - Names that exist as both tags and branches
        - Hash prefixes that match multiple stored objects
    """
    candidates: list[Optional[str]] = list()
    hashRE = re.compile(r"^[0-9A-Fa-f]{4,40}$")

    if not name.strip():
        return None

    if name == "HEAD":
        return [ref_resolve(repo, "HEAD")]

    # Try to resolve as SHA hash (full or partial)
    if hashRE.match(name):
        name = name.lower()
        prefix = name[0:2]
        path = repo_dir(repo, "objects", prefix, mkdir=False)
        if path:
            rem = name[2:]  # Remaining characters after prefix
            for f in os.listdir(path):
                if f.startswith(rem):
                    candidates.append(prefix + f)

    as_tag = ref_resolve(repo, "refs/tags/" + name)
    if as_tag:
        candidates.append(as_tag)

    as_branch = ref_resolve(repo, "refs/heads/" + name)
    if as_branch:
        candidates.append(as_branch)

    as_remote_branch = ref_resolve(repo, "refs/remotes/" + name)
    if as_remote_branch:
        candidates.append(as_remote_branch)

    return candidates
