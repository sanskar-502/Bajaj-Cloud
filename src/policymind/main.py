import logging
import sys

import uvicorn

from policymind.app import app
from policymind.core.config import Settings
from policymind.core.logging import setup_logging


def main() -> None:
    try:
        settings = Settings()
        setup_logging(settings.LOG_LEVEL)
        logger = logging.getLogger(__name__)
        logger.info("Starting PolicyMind...")
        logger.info("=" * 50)
        logger.info("LLM Provider       : %s", settings.LLM_PROVIDER)
        logger.info("Vector DB Type     : %s", settings.VECTOR_DB_TYPE)
        if settings.VECTOR_DB_TYPE == "pinecone" and settings.PINECONE_EMBEDDING_MODEL:
            logger.info("Embedding Model    : %s (Cloud-Hosted)", settings.PINECONE_EMBEDDING_MODEL)
        else:
            logger.info("Embedding Model    : %s (Self-Hosted)", settings.EMBEDDING_MODEL)
        logger.info("API Server listening on http://%s:%s", settings.API_HOST, settings.API_PORT)
        logger.info("=" * 50)
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
        )
    except ValueError as exc:
        logging.getLogger(__name__).error("Configuration Error: %s", str(exc))
        sys.exit(1)
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutting down gracefully...")
    except Exception as exc:
        logging.getLogger(__name__).critical("Application failed to start: %s", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()

