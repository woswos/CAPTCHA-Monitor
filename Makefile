# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: down build up test check

build:
	docker-compose build

up:
	docker-compose up -d

temp:
	docker-compose up

down:
	docker-compose down --remove-orphans

test: up
	docker-compose run --rm --no-deps --entrypoint=pytest captchamonitor /tests

logs:
	docker-compose logs --tail=100 captchamonitor

init:
	pip3 install -U pytest-cov
	sudo apt install black pylint
	
check: check_non_root
	black $$(find * -name '*.py')
	pylint -v $$(find * -name '*.py' -not -path "tests/*")

check_non_root:
ifeq ($(shell id -u), 0)
	@echo "Please run this command without sudo"
	exit 1
endif