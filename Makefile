# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: init down build up

build:
	docker-compose build

up:
	docker-compose up -d --scale cm-worker=5

temp:
	docker-compose up --scale cm-worker=5

down:
ifneq ($(shell docker ps -f ancestor="captchamonitor-tor-container" -q),)
	@echo "\n>> Killing captchamonitor-tor-container instances"
	docker kill $$(sudo docker ps -f ancestor="captchamonitor-tor-container" -q)
endif
	docker-compose down --remove-orphans

test: down
	docker-compose up -d --scale cm-worker=0
	docker-compose run --rm --no-deps --entrypoint="pytest -v --reruns 3 --reruns-delay 3 --cov=/src/captchamonitor/ --cov-report term-missing" captchamonitor /tests

logs:
	docker-compose logs --tail=100 captchamonitor cm-worker

init: check_root
	apt install python3-pip mypy
	pip3 install darglint black pylint isort sphinx sphinx-autodoc-typehints

docs: check_non_root FORCE
	pip3 install -e src/
	sphinx-apidoc -o ./docs/sphinx/ ./src/captchamonitor/
	sphinx-build -b html ./docs/sphinx/ public

check: check_non_root
	@echo "\n\e[93m>> Installing requirements\e[0m"
	pip3 install -q -r requirements.txt
	@echo "\n\e[93m>> Running isort\e[0m"
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