from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    target_site_url: str
    target_sales_url: str
    target_login_id: str
    target_login_pw: str
    frontend_origin: str = "http://localhost:3000"
    # 내부 호출자(whale-erp-api)와 공유하는 HMAC 서명 시크릿. 미설정 시 서명 검증 비활성(개발/점진 배포).
    scrape_api_secret: str = ""
    # 서명 timestamp 허용 시간창(초). 이 범위를 벗어난 요청은 만료로 간주해 거부.
    scrape_sig_window_seconds: int = 300

    model_config = {"env_file": ".env"}


settings = Settings()
