from enum import StrEnum


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    RETRY_WAIT = "retry_wait"
    SUCCESS = "success"
    DEAD_LETTER = "dead_letter"


class OutboxWorkerPhase(StrEnum):
    STARTING = "starting"
    IDLE = "idle"
    WORKING = "working"
    OFFLINE_WAIT = "offline_wait"
    STOPPED = "stopped"
