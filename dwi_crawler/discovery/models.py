"""Search result data models for discovery."""

from datetime import datetime
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Normalized search result item produced by search providers."""
    url: str
    title: str = ""
    description: str = ""
    search_provider: str
    query: str
    keyword: str = ""
    company: str = ""
    source_type: str = "onion"  # "surface" or "onion"
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 0.75
