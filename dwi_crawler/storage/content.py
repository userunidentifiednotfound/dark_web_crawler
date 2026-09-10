"""Content-Addressable Storage (CAS) for raw page source preservation."""

import os
from pathlib import Path
from dwi_crawler.config.settings import get_settings
from dwi_crawler.storage.hashes import sha256_bytes


class ContentAddressableStorage:
    """Stores complete raw page source safely by content hash."""

    def __init__(self, base_path: Path | None = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.storage_path) / "pages"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_rel_path(self, content_hash: str, ext: str = "html") -> str:
        # e.g., ab/cd/abcdef...html
        prefix_1 = content_hash[:2]
        prefix_2 = content_hash[2:4]
        return f"{prefix_1}/{prefix_2}/{content_hash}.{ext}"

    def store_content(self, raw_bytes: bytes, mime_type: str = "text/html") -> tuple[str, str, int]:
        """Saves content using CAS.
        
        Returns:
            (content_hash, relative_uri, byte_size)
        """
        content_hash = sha256_bytes(raw_bytes)
        ext = "html"
        if "json" in mime_type:
            ext = "json"
        elif "xml" in mime_type:
            ext = "xml"
        elif "text" not in mime_type:
            ext = "bin"

        rel_path = self._get_rel_path(content_hash, ext=ext)
        full_path = self.base_path / rel_path

        # If already stored on disk, avoid writing duplicate data
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(raw_bytes)

        return content_hash, str(rel_path), len(raw_bytes)

    def retrieve_content(self, relative_uri: str) -> bytes:
        """Retrieves raw content from CAS."""
        full_path = self.base_path / relative_uri
        if not full_path.exists():
            raise FileNotFoundError(f"Content not found at {full_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def retrieve_by_hash(self, content_hash: str, ext: str = "html") -> bytes | None:
        """Retrieves content by content hash."""
        rel_path = self._get_rel_path(content_hash, ext=ext)
        full_path = self.base_path / rel_path
        if not full_path.exists():
            # Try finding any file with this hash
            prefix_1 = content_hash[:2]
            prefix_2 = content_hash[2:4]
            dir_path = self.base_path / prefix_1 / prefix_2
            if dir_path.exists():
                for p in dir_path.glob(f"{content_hash}.*"):
                    with open(p, "rb") as f:
                        return f.read()
            return None
        with open(full_path, "rb") as f:
            return f.read()

    def retrieve_text(self, content_hash: str, ext: str = "html") -> str | None:
        """Retrieves content as decoded UTF-8 string."""
        raw = self.retrieve_by_hash(content_hash, ext=ext)
        if raw is None:
            return None
        return raw.decode("utf-8", errors="replace")

    def content_exists(self, content_hash: str, ext: str = "html") -> bool:
        rel_path = self._get_rel_path(content_hash, ext=ext)
        return (self.base_path / rel_path).exists()


_storage_instance: ContentAddressableStorage | None = None


def get_content_storage() -> ContentAddressableStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ContentAddressableStorage()
    return _storage_instance
