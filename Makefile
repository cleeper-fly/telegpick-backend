IMAGE_PATH := ${CI_REGISTRY}/telegpick-backend
DOCKERFILE_PATH := ./docker
DOCKERFILE := $(DOCKERFILE_PATH)/Dockerfile

VCS_REF = $(shell git rev-parse --short HEAD)
TAG_NAME ?= dev-${VCS_REF}
BUILD_DATE = $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

.login:
	${INFO} "Logging in to Registry..."
	@docker login --username ${CI_REGISTRY_USER} --password ${CI_REGISTRY_PASSWORD} ${CI_REGISTRY}
	${INFO} "Logged in"

.PHONY: build start stop restart status logs

build: .login
	${INFO} "Building app..."
	@DOCKER_BUILDKIT=1 docker build -f "${DOCKERFILE}" -t "${IMAGE_PATH}:${TAG_NAME}" --build-arg VCS_REF="${VCS_REF}" --build-arg BUILD_DATE="${BUILD_DATE}" .
	${INFO} "Built"
	${INFO} "Pushing app to docker registry..."
	@docker push "${IMAGE_PATH}:${TAG_NAME}"
	${INFO} "Pushed"

start:
	${INFO} "Starting..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) --profile all up -d --force-recreate --build
	${INFO} "Started!"

stop:
	${INFO} "Stopping..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) --profile all down -v
	${INFO} "Stopped!"

restart:
	${INFO} "Restarting..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) --profile all restart
	${INFO} "Restarted!"

configure:
	${INFO} "Migrating db..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) --profile all run --rm --entrypoint alembic backend-app upgrade head
	${INFO} "Done"

update_backend:
	${INFO} "Updating backend..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) --profile backend up -d --force-recreate --no-deps
    #@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) exec web service nginx reload
	${INFO} "Done"

status:
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) ps

logs:
	${INFO} "Logging project..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) logs -f --tail=1000 $(LOG_APP)


YELLOW := "\e[1;33m"
NC := "\e[0m"

INFO := @sh -c '\
    printf $(YELLOW); \
    echo "=> $$1"; \
    printf $(NC)' VALUE


