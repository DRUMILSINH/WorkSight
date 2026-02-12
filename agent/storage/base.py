from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    Allows swapping local / cloud storage without changing agent logic.
    """

    @abstractmethod
    def save(self, file_path):
        """
        Persist a file and return its stored path or identifier.
        """
        raise NotImplementedError
