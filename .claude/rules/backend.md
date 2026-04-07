---
globs:
  - "backend/**"
---

# Backend Rules (FastAPI)

## 실행
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## API Endpoints
```
POST /api/scrape          # 스크래핑 트리거 {start_date, end_date}
GET  /api/sales           # 매출 목록 (start_date, end_date, acquirer, page, page_size)
                          # 응답: { data: CardSale[], total_count: number }
GET  /api/sales/summary   # 매입사별 요약 (start_date, end_date)
```

## 환경변수
`backend/.env` 필요 (`.env.example` 참조):
- `SUPABASE_URL`, `SUPABASE_KEY` — Supabase 접속 정보
- `TARGET_SITE_URL`, `TARGET_SALES_URL` — Bizzle 로그인/매출 페이지 URL
- `TARGET_LOGIN_ID`, `TARGET_LOGIN_PW` — Bizzle 로그인 자격증명

## 구조
- `app/main.py` — FastAPI 앱, CORS (localhost:3000 허용)
- `app/config.py` — pydantic-settings 기반 환경변수
- `app/database.py` — Supabase 클라이언트 초기화
- `app/models.py` — Pydantic 모델 (CardSale, ScrapeRequest/Response, SalesSummary)
- `app/routers/` — API 라우터 (scraper, sales)
- `app/services/` — 비즈니스 로직 (scraper)

## 주의사항
- sales 조회 시 `select("*", count="exact")`로 총 건수를 반환해야 프론트엔드 페이지네이션이 동작한다.
- venv는 `backend/venv/`에 위치. Python 3.13 사용.
