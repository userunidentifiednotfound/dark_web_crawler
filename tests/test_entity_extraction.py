"""Unit tests for threat indicator entity extraction (IOCs)."""

from dwi_crawler.processing.entities import EntityExtractor


def test_extract_emails():
    sample = "Contact admin@targetcorp.com or security-team@corp.io for inquiries."
    entities = EntityExtractor.extract_entities(sample)
    emails = [e.value for e in entities if e.entity_type == "email"]
    assert "admin@targetcorp.com" in emails
    assert "security-team@corp.io" in emails


def test_extract_crypto_wallets():
    sample = """
    Ransom payment details:
    BTC Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
    Bech32 BTC: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq
    Monero XMR: 44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otXft3XjRPUbQGQsA762BaLTemWh9KAoCzKRVT53Q5n2fiEvau1KD
    Ethereum: 0x71C6634C2556405871137A4B110ca679acbCC0E8
    """
    entities = EntityExtractor.extract_entities(sample)
    by_type = {e.entity_type: [] for e in entities}
    for e in entities:
        by_type[e.entity_type].append(e.value)

    assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in by_type.get("crypto_btc", [])
    assert "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq" in by_type.get("crypto_btc", [])
    assert "44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otXft3XjRPUbQGQsA762BaLTemWh9KAoCzKRVT53Q5n2fiEvau1KD" in by_type.get("crypto_xmr", [])
    assert "0x71C6634C2556405871137A4B110ca679acbCC0E8" in by_type.get("crypto_eth", [])


def test_extract_hashes_and_ips():
    sample = """
    Exfiltrated archive md5: 5d41402abc4b2a76b9719d911017c592
    SHA256 signature: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
    Database internal gateway IP: 198.51.100.45
    """
    entities = EntityExtractor.extract_entities(sample)
    values = {e.value: e.entity_type for e in entities}

    assert values.get("5d41402abc4b2a76b9719d911017c592") == "hash_md5"
    assert values.get("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824") == "hash_sha256"
    assert values.get("198.51.100.45") == "ipv4"
