from broadcaster import Broadcast

from src.config import REDIS_URL

REDIS_URL = REDIS_URL

broadcast = Broadcast(REDIS_URL)
