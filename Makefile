# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: init down build up

build:
	@echo "\e[93m>> Building the containers\e[0m"
	docker-compose build

up:
	@echo "\e[93m>> Running all of the containers\e[0m"
	docker-compose up -d --scale cm-worker=3 --scale cm-update=1 --scale cm-analyzer=1

down:
	@echo "\e[93m>> Shutting down the containers\e[0m"
ifneq ($(shell docker ps -f ancestor="captchamonitor-tor-container" -q),)
	@echo "\e[93m>> Killing captchamonitor-tor-container instances\e[0m"
	docker kill $$(sudo docker ps -f ancestor="captchamonitor-tor-container" -q)
endif
	docker-compose down --remove-orphans

test: pretest
	@echo "\e[93m>> Executing all tests\e[0m"
	docker-compose run --rm --no-deps --entrypoint="pytest -v --reruns 3 --reruns-delay 3 --cov=/src/captchamonitor/ --cov-report term-missing" captchamonitor /tests

pretest: down
	@echo "\e[93m>> Preparing the containers for testing\e[0m"
	docker-compose up -d --scale cm-worker=0 --scale cm-update=0 --scale cm-analyzer=0

singletest:
ifndef TEST
	@echo "\e[93m>> TEST is undefined. Please set TEST environment variable to the name of the TEST to execute\e[0m"
	@echo "\e[93m>> Example usage: TEST=test_onionoo_init make singletest\e[0m"
	exit 1
endif
	@echo "\e[93m>> Executing test '$(TEST)'\e[0m"
	docker-compose run --rm --no-deps --entrypoint="pytest -v -x -s -k $(TEST)" captchamonitor /tests

logs:
	@echo "\e[93m>> Printing the logs\e[0m"
	docker-compose logs --tail=100 captchamonitor cm-worker cm-update cm-analyzer

init: check_root
	@echo "\e[93m>> Creating .env file\e[0m"
	rm -f .env
	cp .env.example .env
	@echo "\n\e[93m>> Installing requirements\e[0m"
	pip3 install -q --upgrade --force-reinstall -r requirements.txt
	@echo "\n\e[93m>> Building Docker images\e[0m"
	make build
	@echo "\n\e[92m>> Done!\e[0m"

docs: check_non_root FORCE
	@echo "\e[93m>> Installing the package\e[0m"
	pip3 install -e src/
	@echo "\n\e[93m>> Generating documentation from docstrings\e[0m"
	sphinx-apidoc -f -o ./docs/sphinx/ ./src/captchamonitor/
	@echo "\n\e[93m>> Building the documentation\e[0m"
	sphinx-build -b html ./docs/sphinx/ public
	@echo "\n\e[92m>> Done!\e[0m"

check: check_non_root
	@echo "\e[93m>> Running isort\e[0m"
	isort --profile black .
	@echo "\n\e[93m>> Running black\e[0m"
	black --line-length 88 $$(find * -name '*.py' 2>&1 | grep -v 'Permission denied')
	@echo "\n\e[93m>> Running mypy\e[0m"
	mypy ./src
	@echo "\n\e[93m>> Running pylint\e[0m"
	pylint -v ./src
	@echo "\n\e[93m>> Running darglint\e[0m"
	darglint -s sphinx -v 2 ./src
	@echo "\n\e[92m>> Everything seems all right!\e[0m"

check_non_root:
ifeq ($(shell id -u), 0)
	@echo "\n>> Please run this command without sudo"
	exit 1
endif

check_root:
ifneq ($(shell id -u), 0)
	@echo "\n>> Please run this command with sudo"
	exit 1
endif

FORCE: ;