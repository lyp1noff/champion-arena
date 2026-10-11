from . import athletes, brackets, external, matches, outbox, settings, tournaments

routers = [
    external.router,
    athletes.router,
    settings.router,
    tournaments.router,
    brackets.router,
    matches.router,
    outbox.router,
]
