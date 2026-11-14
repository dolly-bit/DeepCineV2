import logging
import logging.config
import os


def configure_logging() -> None:
    """Configure predictable console logging for local and hosted environments."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        level = "INFO"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {"level": level, "propagate": True},
            "uvicorn.error": {"level": level, "propagate": True},
            "uvicorn.access": {"level": "WARNING", "propagate": True},
            "deepcine": {"level": level, "propagate": True},
        },
    })
