from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    class Config:
        env_file = ".env"


settings = Settings()