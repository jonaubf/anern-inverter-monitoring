.PHONY: deps install clean build_clean dist_clean tests dist docker

ENV=.env
PYTHON_VERSION=3
PYTHON=python${PYTHON_VERSION}
SITE_PACKAGES=${ENV}/lib/${PYTHON}/site-packages
IN_ENV=. ${ENV}/bin/activate;
PACKAGE_VERSION=$(shell cat VERSION)

default: ${ENV} deps

${ENV}:
	@echo "Creating Python environment..." >&2
	@${PYTHON} -m venv ${ENV}
	@echo "Updating pip..." >&2
	@${IN_ENV} ${PYTHON} -m pip install -U pip setuptools

${SITE_PACKAGES}/aiohttp: ${ENV}
	@${IN_ENV} ${PYTHON} -m pip install -r requirements.txt

${SITE_PACKAGES}/anern_monitoring: ${ENV} install

deps: ${SITE_PACKAGES}/aiohttp

install: default
	@${IN_ENV} ${PYTHON} -m pip install -e .

wheel: ${ENV}
	@${IN_ENV} ${PYTHON} -m pip install -U wheel
	@${IN_ENV} ${PYTHON} setup.py bdist_wheel

dist: wheel

dist_clean:
	@rm -rf dist

build_clean:
	@rm -rf build

clean: build_clean dist_clean
	@rm -rf ${ENV} dist build __pycache__ *.egg-info

docker: build_clean dist_clean wheel
	@docker build -t anern_monitoring:${PACKAGE_VERSION} .
	@docker tag anern_monitoring:${PACKAGE_VERSION} anern_monitoring:latest