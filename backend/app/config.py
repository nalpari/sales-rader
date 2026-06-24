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

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]


settings = Settings()
