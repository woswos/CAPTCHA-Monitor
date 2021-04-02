# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: down build up

build:
	docker-compose build

up:
	docker-compose up -d

temp:
	docker-compose up

down:
	docker-compose down --remove-orphans

test: up
	docker-compose run --rm --no-deps --entrypoint="pytest --cov=/src/captchamonitor/ --cov-report term-missing" captchamonitor /tests

logs:
	docker-compose logs --tail=100 captchamonitor

init: check_root
	apt install black pylint
	
check: check_non_root
	pip3 install -q -r requirements.txt
	black --line-length 88 $$(find * -name '*.py')
	pylint -v --disable=C0301,R0903,R0913,C0114,R0902 --docstring-min-length=10 $$(find * -name '*.py' -not -path "tests/*")

check_non_root:
ifeq ($(shell id -u), 0)
	@echo "Please run this command without sudo"
	exit 1
endif

check_root:
ifneq ($(shell id -u), 0)
	@echo "Please run this command with sudo"
	exit 1
endif