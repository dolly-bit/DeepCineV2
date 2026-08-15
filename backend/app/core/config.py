from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    TMDB_API_KEY: str = ""
    TMDB_ACCESS_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()