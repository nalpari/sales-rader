from fastapi import APIRouter
from app.models import ScrapeRequest, ScrapeResponse
from app.services.scraper import scrape_card_sales, scrape_sale_dep

router = APIRouter(prefix="/api", tags=["scraper"])


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: ScrapeRequest):
    """카드매출 스크래핑 수동 트리거 (거래단위 → Supabase 저장)"""
    result = await scrape_card_sales(request.start_date, request.end_date)
    return result


@router.post("/scrape-aggregate")
async def trigger_scrape_aggregate(request: ScrapeRequest):
    """카드매출 집계(getSaleDepMonth) 스크래핑 → Bizzle resobj 패스스루.

    whale-erp 일/월별 집계 화면용. 응답은 Bizzle 원본 그대로:
    `{ "resobj": { "OBJ": { "USER": {...}, "SALE_LIST": [...] } } }`

    login_id/login_pw 가 오면 해당 사용자 계정으로 로그인(없으면 .env 폴백).
    """
    return await scrape_sale_dep(
        request.start_date, request.end_date, request.login_id, request.login_pw
    )
