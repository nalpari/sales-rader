from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from app.models import (
    ScrapeRequest,
    ScrapeResponse,
    ImportKeyRequest,
    ImportKeyResponse,
)
from app.services.scraper import scrape_card_sales, scrape_sale_dep
from app.services.import_key_store import import_key_store

router = APIRouter(prefix="/api", tags=["scraper"])


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: ScrapeRequest):
    """카드매출 스크래핑 수동 트리거 (거래단위 → Supabase 저장)"""
    result = await scrape_card_sales(request.start_date, request.end_date)
    return result


@router.post("/import-key", response_model=ImportKeyResponse)
async def issue_import_key(request: ImportKeyRequest):
    """1회용 import key 발급 (TTL 60s). whale-erp-api 경유로만 호출됨."""
    key = import_key_store.issue(request.year, request.month)
    return ImportKeyResponse(key=key)


@router.post("/scrape-aggregate")
async def trigger_scrape_aggregate(
    request: ScrapeRequest,
    x_sales_import_key: str | None = Header(default=None, alias="X-Sales-Import-Key"),
):
    """카드매출 집계(getSaleDepMonth) 스크래핑 → Bizzle resobj 패스스루.

    whale-erp 일/월별 집계 화면용. 응답은 Bizzle 원본 그대로:
    `{ "resobj": { "OBJ": { "USER": {...}, "SALE_LIST": [...] } } }`

    login_id/login_pw 가 오면 해당 사용자 계정으로 로그인(없으면 .env 폴백).

    진입부에서 1회용 import key 를 검증·소멸한다. 실패 시 Bizzle 을 건드리기 전에 419 반환.
    """
    # key 바인딩은 (year, month). start_date 가 항상 해당 월 1일이므로 거기서 도출해 대조한다.
    year, month = request.start_date.year, request.start_date.month
    if not x_sales_import_key or not import_key_store.consume(
        x_sales_import_key, year, month
    ):
        return JSONResponse(
            status_code=419,
            content={
                "code": "INVALID_IMPORT_KEY",
                "message": "잘못된 데이터 가져오기 방식입니다.",
            },
        )
    return await scrape_sale_dep(
        request.start_date, request.end_date, request.login_id, request.login_pw
    )
