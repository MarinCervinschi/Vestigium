import zlib
import hashlib
from dataclasses import dataclass
from abc import ABC, abstractmethod
from src.core.repository import VesRepository


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
