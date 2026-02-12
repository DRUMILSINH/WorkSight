from pathlib import Path
from agent.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.
    """

    def save(self, file_path):
        """
        For local storage, the file is already saved.
        Just return the absolute path as string.
        """
        return str(Path(file_path).resolve())
