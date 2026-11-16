from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    TMDB_API_KEY: str = ""
    TMDB_ACCESS_TOKEN: str = ""

    # Comma-separated list of allowed frontend origins, e.g.
    # "https://deepcine.vercel.app,https://www.deepcine.app". Defaults to
    # "*" (allow everything) so local dev keeps working with no setup -
    # set this explicitly in production so the API isn't wide open to
    # every origin on the internet.
    ALLOWED_ORIGINS: str = "*"

    # Shared-secret token for the /admin/* endpoints (see
    # app/routes/admin.py) - lets you trigger seeding/index-rebuild over
    # HTTP without needing shell access, which free-tier hosting plans
    # often don't include. Leave blank to disable these endpoints
    # entirely (they 503 if called with no token set).
    ADMIN_TASK_TOKEN: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]

        origins = []
        for origin in self.ALLOWED_ORIGINS.split(","):
            # Defensively normalize the most common copy-paste mistakes:
            # a trailing slash (browsers never send one in the Origin
            # header, so "https://site.com/" would never match) and
            # accidental surrounding quotes from pasting into a
            # dashboard field.
            cleaned = origin.strip().strip('"').strip("'").rstrip("/")
            if cleaned:
                origins.append(cleaned)

        return origins



settings = Settings()