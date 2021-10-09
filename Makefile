PACKAGE_NAME := flask_rl
MODULE_NAME := flask_rl.py
MODULE_TEST_NAME := tests

ifeq ($(VERSION),)
VERSION := 0.0.1
endif
ifeq ($(commit_message),)
commit_message := default commit message
endif
ifeq ($(BRANCH_NAME),)
BRANCH_NAME := main
endif

save:
	@echo "saving..." && git add . && git commit -m "${commit_message}"

save-remote:
	@echo "saving to remote..." && git push origin ${BRANCH_NAME}

release:
	git tag -d ${VERSION} || : && git push --delete origin ${VERSION} || : && git tag -a ${VERSION} -m "latest" && git push origin --tags

test:
	@echo "running tests..." && python3 -m pytest tests

format:
	@echo "formatting..." && python3 -m black ${MODULE_NAME} && python3 -m black ${MODULE_TEST_NAME}

lint:
	@echo "linting..." && python3 -m pylint ${MODULE_NAME} && python3 -m pylint ${MODULE_TEST_NAME}

prettify: format lint

docs-build:
	@echo "building docs..." && python3 -m pdoc ${MODULE_NAME} -o docs

docs-serve:
	python3 -m pdoc ${MODULE_NAME}