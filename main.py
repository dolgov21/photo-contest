import asyncio

from loguru import logger

from app.web.app import start_app


async def main():
    await start_app("etc/config.yaml")


if __name__ == "__main__":
    logger.add(
        "logs/app.log",
        rotation="5MB",
        compression="zip",
        level="DEBUG",
        enqueue=True
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
