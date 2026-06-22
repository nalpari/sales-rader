import logging

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

logger = logging.getLogger("scrape_aggregate")

router = APIRouter(prefix="/api", tags=["scraper"])


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: ScrapeRequest):
    """카드매출 스크래핑 수동 트리거 (거래단위 → Supabase 저장)"""
    result = await scrape_card_sales(request.start_date, request.end_date)
    return result


@router.post("/import-key", response_model=ImportKeyResponse)
async def issue_import_key(request: ImportKeyRequest):
    """1회용 import key 발급 (TTL 60s).

    이 엔드포인트 자체에는 인증/네트워크 제한이 없다. 접근 제한은 sales-rader 가
    `127.0.0.1` 로 호스트 바인딩(docker-compose `127.0.0.1:7000:8000`)되어 외부에서
    직접 닿지 못하는 것으로 이뤄지며, 호출은 whale-erp-api 경유를 의도한다.
    """
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
    # key 는 (year, month) 에 바인딩된다. start_date 에서 연·월만 추출해 대조한다(일자는 무시).
    year, month = request.start_date.year, request.start_date.month
    if not x_sales_import_key:
        reason = "missing_header"
    elif not import_key_store.consume(x_sales_import_key, year, month):
        reason = "invalid_or_expired_key"  # 미존재·만료·(year,month) 불일치 포함
    else:
        reason = None
    if reason is not None:
        # Bizzle 호출 전 거부. key 값은 로깅하지 않는다.
        logger.warning(
            "scrape-aggregate import-key 거부: reason=%s year=%s month=%s",
            reason,
            year,
            month,
        )
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
