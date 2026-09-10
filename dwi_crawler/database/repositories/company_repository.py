"""Repository for managing companies, assets, and keywords."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from dwi_crawler.models.company import Company, CompanyAsset, Keyword, KeywordVariant


class CompanyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, company_id: int) -> Company | None:
        """Loads a company with its assets and active keywords."""
        stmt = (
            select(Company)
            .where(Company.id == company_id)
            .options(
                selectinload(Company.assets),
                selectinload(Company.keywords).selectinload(Keyword.variants),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Company | None:
        stmt = select(Company).where(Company.name == name.strip())
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_companies(self) -> list[Company]:
        stmt = select(Company).order_by(Company.name.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_company(self, name: str, description: str | None = None) -> Company:
        existing = await self.get_by_name(name)
        if existing:
            return existing
        company = Company(name=name.strip(), description=description)
        self.session.add(company)
        await self.session.flush()
        return company

    async def add_asset(self, company_id: int, asset_type: str, value: str) -> CompanyAsset:
        stmt = select(CompanyAsset).where(
            CompanyAsset.company_id == company_id,
            CompanyAsset.asset_type == asset_type.strip(),
            CompanyAsset.value == value.strip(),
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing
        asset = CompanyAsset(company_id=company_id, asset_type=asset_type.strip(), value=value.strip())
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def list_assets(self, company_id: int) -> list[CompanyAsset]:
        stmt = select(CompanyAsset).where(CompanyAsset.company_id == company_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_keyword(self, company_id: int, term: str, category: str = "general") -> Keyword:
        stmt = select(Keyword).where(
            Keyword.company_id == company_id,
            Keyword.term == term.strip(),
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing
        keyword = Keyword(company_id=company_id, term=term.strip(), category=category)
        self.session.add(keyword)
        await self.session.flush()
        return keyword

    async def list_keywords(self, company_id: int) -> list[Keyword]:
        stmt = (
            select(Keyword)
            .where(Keyword.company_id == company_id)
            .options(selectinload(Keyword.variants))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_keyword_variant(self, keyword_id: int, variant: str, variant_type: str) -> KeywordVariant:
        stmt = select(KeywordVariant).where(
            KeywordVariant.keyword_id == keyword_id,
            KeywordVariant.variant == variant.strip(),
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing
        v = KeywordVariant(keyword_id=keyword_id, variant=variant.strip(), variant_type=variant_type)
        self.session.add(v)
        await self.session.flush()
        return v
