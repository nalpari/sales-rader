from fastapi import APIRouter
from app.models import ScrapeRequest, ScrapeResponse
from app.services.scraper import scrape_card_sales

router = APIRouter(prefix="/api", tags=["scraper"])


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: ScrapeRequest):
    """카드매출 스크래핑 수동 트리거"""
    result = await scrape_card_sales(request.start_date, request.end_date)
    return result
