from pydantic_settings import BaseSettings


def _parse_cors_origins(value: str) -> list[str]:
    """Parse a comma-separated CORS origins string into a list."""
    if not value or value.strip() == "*":
        return ["*"]
    return [o.strip() for o in value.split(",") if o.strip()]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/irrigation"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    OPENWEATHERMAP_API_KEY: str = ""
    OPENWEATHERMAP_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    APP_NAME: str = "Verdant"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origin_list(self) -> list[str]:
        return _parse_cors_origins(self.CORS_ORIGINS)


settings = Settings()
