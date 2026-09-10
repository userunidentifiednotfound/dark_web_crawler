"""Unit tests for Content Addressable Storage (CAS)."""

import tempfile
from pathlib import Path
from dwi_crawler.storage.content import ContentAddressableStorage
from dwi_crawler.storage.hashes import sha256_bytes, sha256_text


def test_cas_store_and_retrieve_text():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas = ContentAddressableStorage(base_path=Path(tmp_dir))
        content = "<html><body><h1>Secret Leak Database</h1></body></html>"
        raw_bytes = content.encode("utf-8")

        chash, rel_uri, bsize = cas.store_content(raw_bytes, mime_type="text/html")
        expected_hash = sha256_bytes(raw_bytes)

        assert chash == expected_hash
        assert bsize == len(raw_bytes)
        assert cas.content_exists(chash, ext="html")

        # Test retrieve by relative URI
        retrieved_raw = cas.retrieve_content(rel_uri)
        assert retrieved_raw == raw_bytes

        # Test retrieve by hash
        retrieved_by_hash = cas.retrieve_by_hash(chash, ext="html")
        assert retrieved_by_hash == raw_bytes

        # Test retrieve text
        retrieved_text = cas.retrieve_text(chash, ext="html")
        assert retrieved_text == content


def test_cas_deduplication():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas = ContentAddressableStorage(base_path=Path(tmp_dir))
        payload = b"Ransomware leak file contents repeated test"

        hash1, uri1, size1 = cas.store_content(payload)
        hash2, uri2, size2 = cas.store_content(payload)

        assert hash1 == hash2
        assert uri1 == uri2
        assert size1 == size2


def test_cas_nonexistent_hash():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas = ContentAddressableStorage(base_path=Path(tmp_dir))
        fake_hash = "0000000000000000000000000000000000000000000000000000000000000000"

        assert not cas.content_exists(fake_hash)
        assert cas.retrieve_by_hash(fake_hash) is None
        assert cas.retrieve_text(fake_hash) is None
