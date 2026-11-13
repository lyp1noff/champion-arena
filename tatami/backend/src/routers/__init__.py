from . import athletes, brackets, external, matches, settings, sync, tournaments

routers = [
    external.router,
    athletes.router,
    settings.router,
    tournaments.router,
    brackets.router,
    matches.router,
    sync.router,
]
