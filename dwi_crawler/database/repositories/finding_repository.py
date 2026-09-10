"""Repository for findings, evidence, intelligence records, and IOC entities."""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from dwi_crawler.models.finding import Entity, EntityObservation, Evidence, Finding, IntelligenceRecord
from dwi_crawler.processing.entities import ExtractedEntity
from dwi_crawler.processing.keywords import KeywordMatch


class FindingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_entities(
        self,
        page_id: int,
        company_id: int,
        entities: list[ExtractedEntity],
    ) -> list[EntityObservation]:
        """Saves unique entities and records page observations."""
        observations: list[EntityObservation] = []
        for e in entities:
            # Check or create entity
            stmt = select(Entity).where(Entity.entity_type == e.entity_type, Entity.value == e.value)
            res = await self.session.execute(stmt)
            ent = res.scalar_one_or_none()

            if not ent:
                ent = Entity(entity_type=e.entity_type, value=e.value)
                self.session.add(ent)
                await self.session.flush()

            obs = EntityObservation(
                entity_id=ent.id,
                page_id=page_id,
                company_id=company_id,
                context=e.context,
                confidence=e.confidence,
                observed_at=datetime.utcnow(),
            )
            self.session.add(obs)
            observations.append(obs)

        await self.session.flush()
        return observations

    async def save_intelligence_record(
        self,
        company_id: int,
        page_id: int,
        match: KeywordMatch,
        url: str,
        source_type: str = "onion",
    ) -> IntelligenceRecord:
        rec = IntelligenceRecord(
            company_id=company_id,
            page_id=page_id,
            keyword_id=match.keyword_id,
            matched_keyword=match.term,
            source_type=source_type,
            url=url,
            context=match.context,
            confidence=match.confidence,
            created_at=datetime.utcnow(),
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def create_finding_with_evidence(
        self,
        company_id: int,
        page_id: int,
        title: str,
        description: str,
        matched_keyword: str,
        source_url: str,
        content_hash: str,
        context: str,
        *,
        severity: str = "HIGH",
        confidence: float = 0.85,
        source_type: str = "onion",
    ) -> tuple[Finding, Evidence]:
        """Creates an actionable finding linked to immutable evidence."""
        now = datetime.utcnow()
        finding = Finding(
            company_id=company_id,
            title=title,
            description=description,
            severity=severity,
            status="NEW",
            confidence=confidence,
            matched_keyword=matched_keyword,
            source_url=source_url,
            source_type=source_type,
            first_seen=now,
            last_seen=now,
            created_at=now,
        )
        self.session.add(finding)
        await self.session.flush()

        evidence = Evidence(
            finding_id=finding.id,
            page_id=page_id,
            content_hash=content_hash,
            source_url=source_url,
            retrieved_at=now,
            matched_text_context=context,
            created_at=now,
        )
        self.session.add(evidence)
        await self.session.flush()
        return finding, evidence

    async def get_finding(self, finding_id: int) -> Finding | None:
        stmt = select(Finding).options(selectinload(Finding.evidence_items)).where(Finding.id == finding_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_findings(self, company_id: int | None = None, limit: int = 50) -> list[Finding]:
        stmt = select(Finding).options(selectinload(Finding.evidence_items))
        if company_id:
            stmt = stmt.where(Finding.company_id == company_id)
        stmt = stmt.order_by(Finding.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
