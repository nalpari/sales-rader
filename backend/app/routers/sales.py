from datetime import date
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.database import supabase
from app.models import CardSale, SalesSummary

router = APIRouter(prefix="/api", tags=["sales"])


def _apply_date_filter(query, start_date: date | None, end_date: date | None):
    if start_date:
        query = query.gte("transaction_date", start_date.isoformat())
    if end_date:
        query = query.lte("transaction_date", f"{end_date.isoformat()}T23:59:59")
    return query


@router.get("/sales")
async def get_sales(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    acquirer: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """카드매출 데이터 목록 조회"""
    query = supabase.table("card_sales").select("*", count="exact")
    query = _apply_date_filter(query, start_date, end_date)
    if acquirer:
        query = query.eq("acquirer", acquirer)

    offset = (page - 1) * page_size
    query = query.order("transaction_date", desc=True).range(offset, offset + page_size - 1)

    result = query.execute()
    return {"data": result.data, "total_count": result.count}


@router.get("/sales/summary", response_model=list[SalesSummary])
async def get_sales_summary(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    """매입사별 매출 요약"""
    query = supabase.table("card_sales").select("*")

    if start_date:
        query = query.gte("transaction_date", start_date.isoformat())
    if end_date:
        query = query.lte("transaction_date", f"{end_date.isoformat()}T23:59:59")

    result = query.execute()

    summary: dict[str, dict] = {}
    for row in result.data:
        company = row["acquirer"]
        if company not in summary:
            summary[company] = {"acquirer": company, "total_amount": 0, "count": 0}
        summary[company]["total_amount"] += row["approval_amount"]
        summary[company]["count"] += 1

    return sorted(summary.values(), key=lambda x: x["total_amount"], reverse=True)
