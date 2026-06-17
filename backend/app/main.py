import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import scraper, sales

# Swagger UI 에셋을 외부 CDN(jsdelivr) 대신 로컬에서 제공한다.
# CDN을 못 받아오는 네트워크에서도 /docs가 정상 렌더링되도록 하기 위함.
app = FastAPI(title="Sales Rader API", version="1.0.0", docs_url=None)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _static_url(filename: str) -> str:
    """정적 에셋 URL에 내용 해시를 쿼리로 붙여 캐시 버스팅한다.
    파일이 변경되면 해시가 바뀌어 브라우저가 새 버전을 받는다."""
    path = STATIC_DIR / filename
    digest = hashlib.md5(path.read_bytes()).hexdigest()[:8] if path.exists() else "0"
    return f"/static/{filename}?v={digest}"


# 에셋 해시는 기동 시 1회만 계산한다.
SWAGGER_JS_URL = _static_url("swagger-ui-bundle.js")
SWAGGER_CSS_URL = _static_url("swagger-ui.css")
SWAGGER_FAVICON_URL = _static_url("favicon.png")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url=SWAGGER_JS_URL,
        swagger_css_url=SWAGGER_CSS_URL,
        swagger_favicon_url=SWAGGER_FAVICON_URL,
    )

app.include_router(scraper.router)
app.include_router(sales.router)


@app.get("/")
async def root():
    return {"message": "Sales Rader API"}
