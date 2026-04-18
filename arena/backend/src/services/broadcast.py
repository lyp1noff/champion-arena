from broadcaster import Broadcast

from src.config import DEV_MODE, REDIS_URL

if DEV_MODE:
    broadcast = Broadcast("memory://")
else:
    broadcast = Broadcast(REDIS_URL)
