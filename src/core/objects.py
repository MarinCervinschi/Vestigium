import zlib
import hashlib
import os
from dataclasses import dataclass
from abc import ABC, abstractmethod
from src.core.repository import VesRepository
from src.core.repository import repo_file
from typing import Optional


@dataclass
class VesObject(ABC):

    def __init__(self, data: bytes) -> None:
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    @abstractmethod
    def serialize(self, repo: VesRepository) -> bytes:
        """
        This function MUST be implemented by subclasses.

        It must read the object's contents from self.data, a byte string, and
        do whatever it takes to convert it into a meaningful representation.
        What exactly that means depends on each subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, data: bytes) -> None:
        """
        This function MUST be implemented by subclasses.

        It must take a byte string, which is the raw data read from the
        object store, and parse it to populate the object's attributes.
        What exactly that means depends on each subclass.
        """
        raise NotImplementedError

    def init(self) -> None:
        pass


def object_read(repo: VesRepository, sha: str) -> Optional[VesObject]:
    path = repo_file(repo, "objects", sha[:2], sha[2:])

    if path == None or not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        object_type = raw.find(b" ")
        fmt = raw[:object_type]

        object_size = raw.find(b"\x00", object_type)
        size = int(raw[object_type:object_size].decode("ascii"))
        if size != len(raw) - object_size - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        match fmt:
            case b"commit":
                c = GitCommit
            case b"tree":
                c = GitTree
            case b"tag":
                c = GitTag
            case b"blob":
                c = GitBlob
            case _:
                raise Exception(f"Unknown type {fmt.decode("ascii")} for object {sha}")

        return c(raw[object_size + 1 :])


class GitCommit(VesObject):

    def serialize(self, repo: VesRepository) -> bytes:
        # TODO: Implement commit serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        # TODO: Implement commit deserialization
        return None


class GitTree(VesObject):
    def serialize(self, repo: VesRepository) -> bytes:
        # TODO: Implement tree serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        # TODO: Implement tree deserialization
        return None


class GitTag(VesObject):
    def serialize(self, repo: VesRepository) -> bytes:
        # TODO: Implement tag serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        # TODO: Implement tag deserialization
        return None


class GitBlob(VesObject):
    def serialize(self, repo: VesRepository) -> bytes:
        # TODO: Implement blob serialization
        return b""

    def deserialize(self, data: bytes) -> None:
        # TODO: Implement blob deserialization
        return None
