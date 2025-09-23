import logging

# from .config import LOG_LEVEL

# Configure logging
# logging.basicConfig(
#     level=getattr(logging, LOG_LEVEL.upper()),
#     format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
# )

# Create logger
# logger = logging.getLogger("champion_arena")

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)
