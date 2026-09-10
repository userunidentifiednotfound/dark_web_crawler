"""Entity extraction engine for threat intelligence indicators."""

import re
from typing import NamedTuple


class ExtractedEntity(NamedTuple):
    entity_type: str
    value: str
    context: str
    confidence: float


# Targeted Threat Intelligence Regular Expressions
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
IPV4_REGEX = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")
BTC_REGEX = re.compile(r"\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[ac-hj-np-z02-9]{38,59})\b")
XMR_REGEX = re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b")
ETH_REGEX = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
SHA256_REGEX = re.compile(r"\b[a-fA-F0-9]{64}\b")
MD5_REGEX = re.compile(r"\b[a-fA-F0-9]{32}\b")
USER_HANDLE_REGEX = re.compile(r"(?<=\s)@[a-zA-Z0-9_]{3,25}\b")


class EntityExtractor:
    """Extracts indicators of compromise (IOCs) and technical identities from crawled content."""

    @classmethod
    def extract_entities(cls, text: str, *, context_radius: int = 60) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []
        seen: set[tuple[str, str]] = set()

        def extract_with_pattern(pattern: re.Pattern, entity_type: str, confidence: float):
            for match in pattern.finditer(text):
                val = match.group(0).strip()
                key = (entity_type, val.lower())
                if key in seen:
                    continue
                seen.add(key)

                # Extract surrounding context
                start = max(0, match.start() - context_radius)
                end = min(len(text), match.end() + context_radius)
                context = text[start:end].replace("\n", " ").strip()

                entities.append(
                    ExtractedEntity(
                        entity_type=entity_type,
                        value=val,
                        context=context,
                        confidence=confidence,
                    )
                )

        # 1. Emails
        extract_with_pattern(EMAIL_REGEX, "email", 0.90)

        # 2. IPv4
        extract_with_pattern(IPV4_REGEX, "ipv4", 0.85)

        # 3. Cryptocurrency Addresses (BTC, XMR, ETH)
        extract_with_pattern(BTC_REGEX, "crypto_btc", 0.95)
        extract_with_pattern(XMR_REGEX, "crypto_xmr", 0.95)
        extract_with_pattern(ETH_REGEX, "crypto_eth", 0.95)

        # 4. Hashes (SHA256, MD5)
        extract_with_pattern(SHA256_REGEX, "hash_sha256", 0.80)
        extract_with_pattern(MD5_REGEX, "hash_md5", 0.70)

        # 5. Usernames (@handle)
        extract_with_pattern(USER_HANDLE_REGEX, "username", 0.75)

        return entities
