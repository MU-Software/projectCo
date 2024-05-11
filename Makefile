include .env.local
export $(shell sed 's/=.*//' .env.local)

MIGRATION_MESSAGE ?= `date +"%Y%m%d_%H%M%S"`
UPGRADE_VERSION ?= head
DOWNGRADE_VERSION ?= -1

MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(dir $(MKFILE_PATH))

ifeq (makemigration,$(firstword $(MAKECMDGOALS)))
  MIGRATION_MESSAGE := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(MIGRATION_MESSAGE):;@:)
endif
MIGRATION_MESSAGE := $(if $(MIGRATION_MESSAGE),$(MIGRATION_MESSAGE),migration)

# Set additional build args for docker image build using make arguments
IMAGE_NAME := projectco
ifeq (docker-build,$(firstword $(MAKECMDGOALS)))
  TAG_NAME := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(TAG_NAME):;@:)
endif
TAG_NAME := $(if $(TAG_NAME),$(TAG_NAME),local)
CONTAINER_NAME = $(IMAGE_NAME)_$(TAG_NAME)_container

ifeq ($(DOCKER_DEBUG),true)
	DOCKER_MID_BUILD_OPTIONS = --progress=plain --no-cache
	DOCKER_END_BUILD_OPTIONS = 2>&1 | tee docker-build.log
else
	DOCKER_MID_BUILD_OPTIONS =
	DOCKER_END_BUILD_OPTIONS =
endif


guard-%:
	@if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

# DB migrations
db-makemigration:
	@poetry run alembic revision --autogenerate -m $(MIGRATION_MESSAGE)

db-upgrade:
	@poetry run alembic upgrade $(UPGRADE_VERSION)

db-downgrade:
	@poetry run alembic downgrade $(DOWNGRADE_VERSION)

# Docker compose setup
docker-compose-up:
	docker-compose -f ./infra/docker-compose.dev.yaml up -d

docker-compose-down:
	docker-compose -f ./infra/docker-compose.dev.yaml down

docker-compose-rm: docker-compose-down
	docker-compose -f ./infra/docker-compose.dev.yaml rm

# Docker image build
# Usage: make docker-build <tag-name:=local>
# if you want to build with debug mode, set DOCKER_DEBUG=true
# ex) make docker-build or make docker-build some_TAG_NAME DOCKER_DEBUG=true
docker-build:
	@docker build \
		-f ./infra/Dockerfile -t $(IMAGE_NAME):$(TAG_NAME) \
		--build-arg GIT_HASH=$(shell git rev-parse HEAD) \
		--build-arg IMAGE_BUILD_DATETIME=$(shell date +%Y-%m-%d_%H:%M:%S) \
		$(DOCKER_MID_BUILD_OPTIONS) $(PROJECT_DIR) $(DOCKER_END_BUILD_OPTIONS)

docker-run: docker-compose-up
	@(docker stop $(CONTAINER_NAME) || true && docker rm $(CONTAINER_NAME) || true) > /dev/null 2>&1
	@docker run -d \
		-p 18000:18000 \
		--volume $(PROJECT_DIR)/.env.docker:/.env \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME):$(TAG_NAME)

# For local environments
local-api: docker-compose-up
	@poetry run python -m src

local-celery: docker-compose-up
	@poetry run python -m src.celery_task worker

local-beat: docker-compose-up
	@poetry run python -m src.celery_task beat

local-flower: docker-compose-up
	@poetry run python -m src.celery_task flower

local-celery-healthcheck: docker-compose-up
	@poetry run python -m src.celery_task healthcheck

prod-run:
	@poetry run gunicorn --bind $(HOST):$(PORT) 'src:create_app()' --worker-class uvicorn.workers.UvicornWorker

# Devtools
hooks-install:
	poetry run pre-commit install

hooks-upgrade:
	poetry run pre-commit autoupdate

hooks-lint:
	poetry run pre-commit run --all-files

lint: hooks-lint  # alias

hooks-mypy:
	poetry run pre-commit run mypy --all-files

mypy: hooks-mypy  # alias

# CLI tools
cli-%:
	@if [[ -z "$*" || "$*" == '.o' ]]; then echo "Usage: make cli-<command>"; exit 1; fi
	poetry run python -m src.cli $*
