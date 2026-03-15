SHELL := /bin/bash
PWD := $(shell pwd)

default: deliver

env-deps:
ifeq ($(origin REPO_PATH),undefined)
	@echo "Error: REPO_PATH env variable is not defined"
	@exit 1
endif
.PHONY: env-deps

test: env-deps
	pytest
.PHONY: test

test-logs: env-deps
	pytest -s
.PHONY: test

deliver: env-deps test
	@echo "TEXTO DE ENTREGA:"
	@(cd ${REPO_PATH}; git config --get remote.origin.url | cut -d ":" -f 2 | rev | cut -d "." -f2 | rev | xargs -I {} echo "Enlace: github.com/{}")
	@echo "Últimos commits:"
	@(cd ${REPO_PATH}; git ls-remote -q) 
.PHONY: deliver
