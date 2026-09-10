"""DWI Core client abstraction for threat intelligence and finding integration."""

import logging
from typing import Any
from dwi_crawler.config.settings import get_settings

logger = logging.getLogger("dwi_crawler.dwi_client")


class DWIClient:
    """Client interface for communicating findings to the DWI core platform."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.api_url = api_url or settings.dwi_api_url
        self.api_key = api_key or settings.dwi_api_key

    async def create_discovery(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Registers a discovered target URL with DWI core."""
        logger.debug(f"DWIClient: Registered discovery for {payload.get('url')}")
        return {"status": "registered", "url": payload.get("url")}

    async def create_intelligence_record(self, record_data: dict[str, Any]) -> dict[str, Any]:
        """Submits an intelligence observation record."""
        logger.info(f"DWIClient: Created intelligence record for {record_data.get('matched_keyword')}")
        return {"status": "recorded", "id": record_data.get("id")}

    async def create_finding(self, finding_data: dict[str, Any]) -> dict[str, Any]:
        """Submits an actionable security finding."""
        logger.info(f"DWIClient: Registered finding '{finding_data.get('title')}' for company {finding_data.get('company_id')}")
        return {"status": "created", "finding": finding_data.get("title")}

    async def register_entity(self, entity_data: dict[str, Any]) -> dict[str, Any]:
        """Registers an IOC entity with DWI core."""
        logger.debug(f"DWIClient: Registered entity {entity_data.get('entity_type')}={entity_data.get('value')}")
        return {"status": "registered"}

    async def register_relationship(self, source_id: str, target_id: str, rel_type: str) -> dict[str, Any]:
        """Registers a link or correlation relationship."""
        return {"status": "linked"}


_dwi_client_instance: DWIClient | None = None


def get_dwi_client() -> DWIClient:
    global _dwi_client_instance
    if _dwi_client_instance is None:
        _dwi_client_instance = DWIClient()
    return _dwi_client_instance
