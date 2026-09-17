.PHONY: help check-runtime tools up down reset logs ps creds seed sample shell odoo-shell psql console

.DEFAULT_GOAL := help

# Detect container runtime (prefer podman)
CONTAINER_RUNTIME = $(or \
	$(shell command -v podman 2>/dev/null), \
	$(shell command -v docker 2>/dev/null) \
)

COMPOSE_FILE := compose.yml
COMPOSE = $(CONTAINER_RUNTIME) compose -f $(COMPOSE_FILE)

# odooly.ini section used by `make console`
ODOOLY_ENV ?= dev

# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@awk 'BEGIN {FS = ":.*?## "; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ General

check-runtime: ## Checks runtime and exits if not found
	@if [ -z "$(CONTAINER_RUNTIME)" ]; then \
		echo "Error: Neither podman nor docker found."; \
		exit 1; \
	fi

tools: ## install pinned CLI tools (odooly) with mise
	mise install

##@ Odoo

up: check-runtime ## start odoo (postgres detached, odoo in foreground)
	@echo "Starting postgres in background..."
	@$(COMPOSE) up -d --wait db
	@echo "Starting odoo in foreground (logs will be visible)..."
	$(COMPOSE) up --build odoo

down: check-runtime ## stop and remove odoo containers (keeps data)
	$(COMPOSE) down

reset: check-runtime ## stop odoo and DELETE all data volumes
	$(COMPOSE) down --volumes --remove-orphans

logs: check-runtime ## view logs from odoo containers
	$(COMPOSE) logs -f

ps: check-runtime ## show odoo container status
	$(COMPOSE) ps

creds: check-runtime ## print credentials of the running odoo
	@$(COMPOSE) exec odoo /opt/oodev/lib/banner.sh

seed: check-runtime ## re-run seeding in the running odoo (STEPS=users,apikeys, DATASETS=crm to limit)
	$(COMPOSE) exec -e SEED_STEPS=$(STEPS) -e SEED_DATASETS=$(DATASETS) odoo /opt/oodev/init-odoo.sh --seed-only

sample: ## load sample datasets through the API with odooly (DATASETS=crm to limit, ODOOLY_ENV)
	OODEV_SEED_DIR=$(CURDIR)/odoo/seed SEED_DATASETS=$(DATASETS) mise exec -- odooly --env $(ODOOLY_ENV) < odoo/seed/run_odooly.py

##@ Shells

shell: check-runtime ## open shell in odoo container
	$(COMPOSE) exec odoo /bin/bash

odoo-shell: check-runtime ## open odoo python shell (with env) in odoo container
	$(COMPOSE) exec odoo odoo shell --no-http

psql: check-runtime ## open psql on the odoo database
	$(COMPOSE) exec odoo psql

console: ## open odooly console on the local odoo (ODOOLY_ENV=dev)
	@command -v mise >/dev/null || { echo "Error: mise not found, see https://mise.jdx.dev"; exit 1; }
	mise exec -- odooly --env $(ODOOLY_ENV)
