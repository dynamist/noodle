.PHONY: help check-tools tools cluster destroy odoo-image deploy up down reset logs ps shell creds seed sample validate test-k8s ci-deploy ci-test odoo-shell psql db-forward console

.DEFAULT_GOAL := help

# Shared k3d cluster, see k8s/cluster/k3d.yaml. Every kubectl call names the
# context explicitly so nothing here ever acts on another cluster.
CLUSTER := dynamist-dev
KUBE_CONTEXT := k3d-$(CLUSTER)
NAMESPACE := oodev
KUBECTL = mise exec -- kubectl --context $(KUBE_CONTEXT) -n $(NAMESPACE)
K3D = mise exec -- k3d

# Kustomize overlay to deploy (local or ci)
OVERLAY ?= local
IMAGE := dynamist/odoo
BUILD_DIR := .k8s

# odooly.ini section used by `make console` and `make sample`
ODOOLY_ENV ?= dev
# Local port for `make db-forward`
POSTGRES_PORT ?= 5432

# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@awk 'BEGIN {FS = ":.*?## "; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ General

check-tools:
	@command -v mise >/dev/null || { echo "Error: mise not found, see https://mise.jdx.dev"; exit 1; }
	@command -v docker >/dev/null || { echo "Error: docker not found, k3d runs the cluster in docker"; exit 1; }

tools: ## install pinned CLI tools (k3d, kubectl, odooly) with mise
	mise install

##@ Cluster

cluster: check-tools ## create the shared k3d cluster, or reuse it
	@if $(K3D) cluster get $(CLUSTER) >/dev/null 2>&1; then \
		echo "Reusing k3d cluster $(CLUSTER)"; \
		$(K3D) cluster start $(CLUSTER) >/dev/null; \
	else \
		$(K3D) cluster create --config k8s/cluster/k3d.yaml; \
	fi
	@pinned=$$(sed -n 's|^image: rancher/k3s:\(.*\)|\1|p' k8s/cluster/k3d.yaml | tr - +); \
	running=$$(mise exec -- kubectl --context $(KUBE_CONTEXT) get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}'); \
	if [ "$$pinned" != "$$running" ]; then \
		echo "WARNING: cluster runs k3s $$running but k8s/cluster/k3d.yaml pins $$pinned, see make destroy"; \
	fi
	@echo "Waiting for the Traefik ingress..."
	@until mise exec -- kubectl --context $(KUBE_CONTEXT) -n kube-system get deploy traefik >/dev/null 2>&1; do sleep 3; done
	@mise exec -- kubectl --context $(KUBE_CONTEXT) -n kube-system rollout status deploy/traefik --timeout=5m

destroy: check-tools ## DELETE the shared cluster with every app and all data (FORCE=1 if other apps run)
	@others=$$(mise exec -- kubectl --context $(KUBE_CONTEXT) get ns -l 'dynamist.se/dev-app,dynamist.se/dev-app!=$(NAMESPACE)' -o name 2>/dev/null); \
	if [ -n "$$others" ] && [ "$(FORCE)" != "1" ]; then \
		echo "Other apps run in the cluster: $$others"; \
		echo "Use make reset to delete only oodev, or make destroy FORCE=1 to delete them too"; \
		exit 1; \
	fi
	$(K3D) cluster delete $(CLUSTER)

##@ Odoo

odoo-image: check-tools ## build the odoo image and import it into the cluster
	docker build -t $(IMAGE):dev .
	@mkdir -p $(BUILD_DIR)
	@# Tag by content, so the deployment only rolls out when the image changed
	@tag=dev-$$(docker image inspect -f '{{.Id}}' $(IMAGE):dev | cut -d: -f2 | cut -c1-12); \
	docker tag $(IMAGE):dev $(IMAGE):$$tag; \
	$(K3D) image import -c $(CLUSTER) $(IMAGE):$$tag; \
	echo $$tag > $(BUILD_DIR)/image-tag

deploy: check-tools ## apply the manifests of OVERLAY (local or ci) with the imported image
	@test -f $(BUILD_DIR)/image-tag || { echo "Error: no image imported yet, run make odoo-image"; exit 1; }
	@touch k8s/overlays/local/config.local.env
	@printf '%s\n' \
		'apiVersion: kustomize.config.k8s.io/v1beta1' \
		'kind: Kustomization' \
		'resources: [../k8s/overlays/$(OVERLAY)]' \
		'images: [{name: $(IMAGE), newTag: '"$$(cat $(BUILD_DIR)/image-tag)"'}]' \
		> $(BUILD_DIR)/kustomization.yaml
	mise exec -- kubectl --context $(KUBE_CONTEXT) apply -k $(BUILD_DIR)

up: cluster odoo-image deploy ## start odoo in the cluster and follow its logs until it is ready
	@$(KUBECTL) rollout status statefulset/db --timeout=5m
	@$(KUBECTL) logs -f deploy/odoo --pod-running-timeout=5m & logs=$$!; \
	$(KUBECTL) rollout status deploy/odoo --timeout=30m; status=$$?; \
	sleep 2; kill $$logs 2>/dev/null; exit $$status

down: check-tools ## stop odoo and postgres, keep data
	$(KUBECTL) scale deploy/odoo statefulset/db --replicas=0

reset: check-tools ## DELETE the oodev namespace with all its data (other apps are untouched)
	mise exec -- kubectl --context $(KUBE_CONTEXT) delete namespace $(NAMESPACE) --ignore-not-found --wait

logs: check-tools ## follow odoo logs
	$(KUBECTL) logs -f deploy/odoo

ps: check-tools ## show pods, services, ingress and volumes
	$(KUBECTL) get pods,svc,ingress,pvc

shell: check-tools ## open shell in the odoo pod
	$(KUBECTL) exec -it deploy/odoo -- /bin/bash

creds: check-tools ## print credentials of the running odoo
	@$(KUBECTL) exec deploy/odoo -- /opt/oodev/lib/banner.sh

seed: check-tools ## copy odoo/seed into odoo and re-run seeding (STEPS=users,apikeys, DATASETS=crm to limit)
	tar -C odoo/seed --exclude=__pycache__ -c . | \
		$(KUBECTL) exec -i deploy/odoo -- sh -c 'rm -rf /tmp/oodev-seed && mkdir /tmp/oodev-seed && tar -x -C /tmp/oodev-seed'
	$(KUBECTL) exec deploy/odoo -- env OODEV_SEED_DIR=/tmp/oodev-seed SEED_STEPS=$(STEPS) SEED_DATASETS=$(DATASETS) \
		/opt/oodev/init-odoo.sh --seed-only

sample: ## load sample datasets through the API with odooly (DATASETS=crm to limit, ODOOLY_ENV)
	OODEV_SEED_DIR=$(CURDIR)/odoo/seed SEED_DATASETS=$(DATASETS) mise exec -- odooly --env $(ODOOLY_ENV) < odoo/seed/run_odooly.py

##@ Test

validate: ## validate the rendered manifests of all overlays
	@touch k8s/overlays/local/config.local.env
	@for overlay in k8s/overlays/*/; do \
		mise exec -- kubectl kustomize $$overlay | mise exec -- kubeconform -strict -summary || exit 1; \
	done

test-k8s: ## run the smoke, seed data and isolation tests in tests/k8s against the deployed odoo (PYTEST_ARGS="-m 'not slow'" for pytest)
	mise exec -- uv run --no-project --with pytest --with requests --with pyyaml \
		pytest tests/k8s -p no:cacheprovider $(PYTEST_ARGS)

##@ CI

# Every app repo using the shared cluster provides ci-deploy and ci-test, so CI
# can deploy other apps next to this one without knowing them

ci-deploy: cluster odoo-image ## build and deploy the ci overlay, wait until it is ready
	$(MAKE) --no-print-directory deploy OVERLAY=ci
	$(KUBECTL) rollout status statefulset/db --timeout=10m
	$(KUBECTL) rollout status deploy/odoo --timeout=40m

ci-test: ## run every test against the deployed ci overlay
	$(MAKE) --no-print-directory test-k8s PYTEST_ARGS="-v"
	$(MAKE) --no-print-directory sample

##@ Shells

odoo-shell: check-tools ## open odoo python shell (with env) in the odoo pod
	$(KUBECTL) exec -it deploy/odoo -- odoo shell --no-http

psql: check-tools ## open psql on the odoo database
	$(KUBECTL) exec -it deploy/odoo -- psql

db-forward: check-tools ## forward postgres to 127.0.0.1:POSTGRES_PORT until Ctrl+C
	$(KUBECTL) port-forward svc/db $(POSTGRES_PORT):5432

console: ## open odooly console on the local odoo (ODOOLY_ENV=dev)
	@command -v mise >/dev/null || { echo "Error: mise not found, see https://mise.jdx.dev"; exit 1; }
	mise exec -- odooly --env $(ODOOLY_ENV)
