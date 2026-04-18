from . import (
    athletes,
    auth,
    brackets,
    categories,
    coaches,
    matches,
    sync,
    tournaments,
    upload,
    websocket,
)

routers = [
    coaches.router,
    athletes.router,
    tournaments.router,
    categories.router,
    brackets.router,
    matches.router,
    sync.router,
    upload.router,
    auth.router,
    websocket.router,
]
