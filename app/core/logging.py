import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """
    Configures structured standard logging for the application.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )

    # Silence overly verbose loggers if needed
    logging.getLogger("uvicorn.access").setLevel(log_level)


logger = logging.getLogger("doc2action")
