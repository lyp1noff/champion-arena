from . import (
    athletes,
    auth,
    brackets,
    categories,
    coaches,
    matches,
    tournaments,
    upload,
)

routers = [
    coaches.router,
    athletes.router,
    tournaments.router,
    categories.router,
    brackets.router,
    matches.router,
    upload.router,
    auth.router,
]
