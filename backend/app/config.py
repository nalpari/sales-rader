from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    target_site_url: str
    target_sales_url: str
    target_login_id: str
    target_login_pw: str
    frontend_origin: str = "http://localhost:3000"

    model_config = {"env_file": ".env"}


settings = Settings()
