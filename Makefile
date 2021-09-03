
ifeq ($(VERSION),)
VERSION := 0.0.1
endif

release:
	git tag -d ${VERSION} || : && git push --delete origin ${VERSION} || : && git tag -a ${VERSION} -m "latest" && git push origin --tags