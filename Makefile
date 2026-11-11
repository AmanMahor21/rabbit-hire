# Makefile for talent-ai-platform
# Dev-mode compose overlays your live ./backend source on top of the image,
# so code changes are picked up without rebuilding the image.

COMPOSE      := docker compose
COMPOSE_BASE := -f docker-compose.yml
COMPOSE_DEV  := -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: help up up-dev down build rebuild restart-api restart-worker \
        logs ps frontend-dev sh-worker clean

help:
	@echo "talent-ai-platform targets:"
	@echo "  make up          - start the full stack (production compose)"
	@echo "  make up-dev      - start stack with live-reload dev overlay (recommended for coding)"
	@echo "  make build       - build images (no deps change; just image layer)"
	@echo "  make rebuild     - force full rebuild (after editing requirements.txt/Dockerfile)"
	@echo "  make down        - stop all containers"
	@echo "  make restart-api - restart only the API (no build, after api code change)"
	@echo "  make restart-worker - restart only the Celery worker (no build)"
	@echo "  make logs        - follow all container logs"
	@echo "  make ps          - list running containers"
	@echo "  make frontend-dev - run the Vite dev server locally (hot reload, no Docker)"
	@echo "  make sh-worker   - open a shell in the worker container"
	@echo "  make clean       - stop everything and remove volumes"

up:
	$(COMPOSE) $(COMPOSE_BASE) up -d --build

up-dev:
	$(COMPOSE) $(COMPOSE_DEV) up -d --build

build:
	$(COMPOSE) $(COMPOSE_BASE) build

rebuild:
	$(COMPOSE) $(COMPOSE_BASE) build --no-cache

down:
	$(COMPOSE) $(COMPOSE_BASE) down

restart-api:
	$(COMPOSE) $(COMPOSE_DEV) restart api

restart-worker:
	$(COMPOSE) $(COMPOSE_DEV) restart worker

logs:
	$(COMPOSE) $(COMPOSE_BASE) logs -f --tail=100

ps:
	$(COMPOSE) $(COMPOSE_BASE) ps

frontend-dev:
	cd frontend && npm run dev

sh-worker:
	$(COMPOSE) $(COMPOSE_DEV) exec worker sh

clean:
	$(COMPOSE) $(COMPOSE_BASE) down -v
