"""Repository for recording search runs and results."""

from sqlalchemy.ext.asyncio import AsyncSession
from dwi_crawler.discovery.models import SearchResultItem
from dwi_crawler.models.job import SearchResult, SearchRun


class SearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_search_run(
        self,
        company_id: int,
        provider: str,
        query: str,
        source_type: str,
        results: list[SearchResultItem],
        *,
        keyword_id: int | None = None,
    ) -> SearchRun:
        run = SearchRun(
            company_id=company_id,
            keyword_id=keyword_id,
            provider=provider,
            query=query,
            source_type=source_type,
            results_count=len(results),
            status="SUCCESS",
        )
        self.session.add(run)
        await self.session.flush()

        for item in results:
            res = SearchResult(
                search_run_id=run.id,
                url=item.url,
                title=item.title,
                description=item.description,
                source_type=item.source_type,
                confidence=item.confidence,
            )
            self.session.add(res)

        await self.session.flush()
        return run
