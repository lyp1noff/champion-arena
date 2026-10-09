SHELL := /bin/bash

DEV_COMPOSE := docker compose --project-name champion-dev -f docker-compose.dev.yml
ARENA_PROD_COMPOSE := docker compose --project-name champion-arena --env-file arena/.env -f docker-compose.yml
TATAMI_PROD_COMPOSE := docker compose --project-name champion-tatami --env-file tatami/.env -f tatami/docker-compose.yml

DB ?= champ
DB_USER ?= user
BACKUP_DIR ?= backups
BACKUP_FILE ?= $(BACKUP_DIR)/$(DB)-$(shell date +%Y%m%d-%H%M%S).sql.gz

.PHONY: dev arena tatami db down logs backup restore prod-arena prod-arena-down prod-arena-logs prod-tatami prod-tatami-down prod-tatami-logs

dev:
	$(DEV_COMPOSE) up -d --build

arena:
	$(DEV_COMPOSE) up -d --build arena-nginx

tatami:
	$(DEV_COMPOSE) up -d --build tatami-nginx tatami-outbox

db:
	$(DEV_COMPOSE) up -d db

down:
	$(DEV_COMPOSE) down

logs:
	$(DEV_COMPOSE) logs --follow $(SERVICE)

backup: db
	@mkdir -p "$(dir $(BACKUP_FILE))"
	@set -o pipefail; \
	$(DEV_COMPOSE) exec -T db pg_dump -U "$(DB_USER)" -d "$(DB)" --no-owner --no-privileges \
		| gzip > "$(BACKUP_FILE)"
	@echo "Backup written to $(BACKUP_FILE)"

restore: db
	@test -n "$(FILE)" || { echo "Usage: make restore DB=champ FILE=backup.sql.gz"; exit 1; }
	@set -o pipefail; \
	case "$(FILE)" in \
		*.sql.gz) gzip -dc "$(FILE)" | $(DEV_COMPOSE) exec -T db psql -v ON_ERROR_STOP=1 -U "$(DB_USER)" -d "$(DB)" ;; \
		*.sql) $(DEV_COMPOSE) exec -T db psql -v ON_ERROR_STOP=1 -U "$(DB_USER)" -d "$(DB)" < "$(FILE)" ;; \
		*.dump.gz|*.backup.gz) gzip -dc "$(FILE)" | $(DEV_COMPOSE) exec -T db pg_restore -U "$(DB_USER)" -d "$(DB)" --clean --if-exists --no-owner --no-privileges ;; \
		*.dump|*.backup) $(DEV_COMPOSE) exec -T db pg_restore -U "$(DB_USER)" -d "$(DB)" --clean --if-exists --no-owner --no-privileges < "$(FILE)" ;; \
		*) echo "Unsupported backup format: $(FILE)"; exit 1 ;; \
	esac

prod-arena:
	$(ARENA_PROD_COMPOSE) up -d

prod-arena-down:
	$(ARENA_PROD_COMPOSE) down

prod-arena-logs:
	$(ARENA_PROD_COMPOSE) logs --follow

prod-tatami:
	$(TATAMI_PROD_COMPOSE) up -d

prod-tatami-down:
	$(TATAMI_PROD_COMPOSE) down

prod-tatami-logs:
	$(TATAMI_PROD_COMPOSE) logs --follow
