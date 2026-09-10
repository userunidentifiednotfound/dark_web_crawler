"""Entity, Intelligence Record, Finding, and Evidence models."""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from dwi_crawler.database.session import Base


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # email, domain, ipv4, ipv6, hash, username, crypto_btc, crypto_xmr, etc.
    value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    observations: Mapped[list["EntityObservation"]] = relationship("EntityObservation", back_populates="entity", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("entity_type", "value", name="uq_entity_type_val"),
    )


class EntityObservation(Base):
    __tablename__ = "entity_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="observations")


class IntelligenceRecord(Base):
    __tablename__ = "intelligence_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("keywords.id", ondelete="SET NULL"), nullable=True, index=True)

    matched_keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="onion")
    url: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(String(50), default="NEW", index=True)  # NEW, INVESTIGATING, CONFIRMED, FALSE_POSITIVE, RESOLVED
    confidence: Mapped[float] = mapped_column(Float, default=0.75)
    matched_keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="onion")

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    company: Mapped["Company"] = relationship("Company", back_populates="findings")  # type: ignore # noqa: F821
    evidence_items: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[int] = mapped_column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    matched_text_context: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="evidence_items")
    page: Mapped["Page"] = relationship("Page", back_populates="evidence")  # type: ignore # noqa: F821
