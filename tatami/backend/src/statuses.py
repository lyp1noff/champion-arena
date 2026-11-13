from enum import StrEnum


class SyncWorkerPhase(StrEnum):
    STARTING = "starting"
    IDLE = "idle"
    SENDING = "sending"
    OFFLINE = "offline"
    STOPPED = "stopped"
