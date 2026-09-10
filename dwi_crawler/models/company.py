"""Company, Asset, and Keyword database models."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from dwi_crawler.database.session import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    assets: Mapped[list["CompanyAsset"]] = relationship("CompanyAsset", back_populates="company", cascade="all, delete-orphan")
    keywords: Mapped[list["Keyword"]] = relationship("Keyword", back_populates="company", cascade="all, delete-orphan")
    discovered_urls: Mapped[list["DiscoveredURL"]] = relationship("DiscoveredURL", back_populates="company", cascade="all, delete-orphan")  # type: ignore # noqa: F821
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="company", cascade="all, delete-orphan")  # type: ignore # noqa: F821


class CompanyAsset(Base):
    __tablename__ = "company_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # domain, subdomain, ip, email, identity, brand
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    company: Mapped["Company"] = relationship("Company", back_populates="assets")

    __table_args__ = (
        UniqueConstraint("company_id", "asset_type", "value", name="uq_company_asset"),
    )


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general")  # brand, executive, product, infrastructure
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    company: Mapped["Company"] = relationship("Company", back_populates="keywords")
    variants: Mapped[list["KeywordVariant"]] = relationship("KeywordVariant", back_populates="keyword", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("company_id", "term", name="uq_company_keyword"),
    )


class KeywordVariant(Base):
    __tablename__ = "keyword_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False, index=True)
    variant: Mapped[str] = mapped_column(String(500), nullable=False)
    variant_type: Mapped[str] = mapped_column(String(50), nullable=False)  # exact, breach, credentials, leak, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    keyword: Mapped["Keyword"] = relationship("Keyword", back_populates="variants")

    __table_args__ = (
        UniqueConstraint("keyword_id", "variant", name="uq_keyword_variant"),
    )
