from . import (
    coaches,
    athletes,
    tournaments,
    categories,
    brackets,
    upload,
    auth,
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
