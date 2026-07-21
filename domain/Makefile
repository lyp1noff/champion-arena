lint:
	uv run ruff check .
	uv run mypy .

format:
	uv run ruff format .

build:
	uv build

release-check: lint build

release: release-check
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Working tree is dirty. Commit or stash changes first."; \
		exit 1; \
	fi
	@VERSION=$$(python -c 'import tomllib;print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])'); \
	TAG="v$$VERSION"; \
	if git rev-parse "$$TAG" >/dev/null 2>&1; then \
		echo "Tag $$TAG already exists."; \
		exit 1; \
	fi; \
	echo "Releasing $$TAG"; \
	git tag "$$TAG"; \
	git push; \
	git push --tags

commit: format lint
