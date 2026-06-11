import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import scraper, sales

app = FastAPI(title="Sales Rader API", version="1.0.0")

if not settings.scrape_api_secret:
    logging.getLogger("uvicorn.error").warning(
        "SCRAPE_API_SECRET 미설정 — /api/scrape* 요청 서명 검증이 비활성화되어 있습니다. "
        "운영 환경에서는 반드시 설정하세요(whale-erp-api 와 동일 값)."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraper.router)
app.include_router(sales.router)


@app.get("/")
async def root():
    return {"message": "Sales Rader API"}
