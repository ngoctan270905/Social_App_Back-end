from loguru import logger
import sys

def setup_logging():
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="{level.icon} <green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
