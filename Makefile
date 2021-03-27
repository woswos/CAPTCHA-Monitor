# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: down build up test check

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down --remove-orphans

test: up
	docker-compose run --rm --no-deps --entrypoint=pytest captchamonitor /tests

logs:
	docker-compose logs --tail=100 captchamonitor

check:
	black $$(find * -name '*.py')
	pylint -v $$(find * -name '*.py')

init:
	pip3 install -U pytest-cov
	sudo apt install black pylint