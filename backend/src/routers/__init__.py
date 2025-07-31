from . import (
    athletes,
    auth,
    brackets,
    categories,
    coaches,
    tournaments,
    upload,
)

routers = [
    coaches.router,
    athletes.router,
    tournaments.router,
    categories.router,
    brackets.router,
    upload.router,
    auth.router,
]
