from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    TMDB_API_KEY: str = ""
    TMDB_ACCESS_TOKEN: str = ""

    # Use "null" with serverless PostgreSQL (for example Neon) so each
    # request closes its database connection instead of leaving an idle
    # connection checked out in SQLAlchemy's local pool.
    DB_POOL_MODE: str = "queue"

    # The in-process scheduler is useful for local development, but should
    # be disabled on a sleeping/free web service. Scheduled work cannot be
    # relied on while the service is scaled down.
    ENABLE_SCHEDULER: bool = True

    # Comma-separated list of allowed frontend origins, e.g.
    # "https://deepcine-v2.vercel.app". Defaults to "*" for local setup.
    ALLOWED_ORIGINS: str = "*"

    # Shared-secret token for the /admin/* endpoints.
    ADMIN_TASK_TOKEN: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]

        origins = []
        for origin in self.ALLOWED_ORIGINS.split(","):
            cleaned = origin.strip().strip('"').strip("'").rstrip("/")
            if cleaned:
                origins.append(cleaned)

        return origins


settings = Settings()
