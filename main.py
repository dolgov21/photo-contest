from loguru import logger

from app.web.app import start_app

if __name__ == "__main__":
    logger.add(
        "logs/app.log",
        rotation="5MB",
        compression="zip",
        level="DEBUG",
        enqueue=True,
    )

    try:
        start_app("etc/config.yaml")
    except KeyboardInterrupt:
        pass
