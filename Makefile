########## for uploading onto pypi
# this assumes you have an entry 'pypi' in your .pypirc
# see pypi documentation on how to create .pypirc

LIBRARY = r2lab

VERSION = $(shell python3 -c "from $(LIBRARY) import __version__; print(__version__)")
VERSIONTAG = $(LIBRARY)-$(VERSION)
GIT-TAG-ALREADY-SET = $(shell git tag | grep '^$(VERSIONTAG)$$')
# to check for uncommitted changes
GIT-CHANGES = $(shell echo $$(git diff HEAD | wc -l))

# run this only once the sources are in on the right tag
pypi:
	@if [ $(GIT-CHANGES) != 0 ]; then echo "You have uncommitted changes - cannot publish"; false; fi
	@if [ -n "$(GIT-TAG-ALREADY-SET)" ] ; then echo "tag $(VERSIONTAG) already set"; false; fi
	@if ! grep -q ' $(VERSION)' CHANGELOG.md ; then echo no mention of $(VERSION) in CHANGELOG.md; false; fi
	@echo "You are about to release $(VERSION) - OK (Ctrl-c if not) ? " ; read _
	git tag $(VERSIONTAG)
	./setup.py sdist upload -r pypi

# it can be convenient to define a test entry, say testpypi, in your .pypirc
# that points at the testpypi public site
# no upload to build.onelab.eu is done in this case
# try it out with
# pip install -i https://testpypi.python.org/pypi $(LIBRARY)
# dependencies need to be managed manually though
testpypi:
	./setup.py sdist upload -r testpypi

##############################
tags:
	git ls-files | xargs etags

.PHONY: tags

############################## for deploying before packaging
# default is to mess with our preplab and let the production
# site do proper upgrades using pip3
deployment ?= preplab

ifeq "$(deployment)" "production"
    DEST=faraday.inria.fr
else
    DEST=preplab.pl.sophia.inria.fr
endif

# installing in /tmp/r2lab-sync for testing
sync:
	@echo 'export PYTHONPATH=/tmp/r2lab-sync'
	rsync -av --relative $$(git ls-files) root@$(DEST):/tmp/r2lab-sync/

faraday:
	$(MAKE) sync deployment=production

preplab:
	$(MAKE) sync deployment=preplab

.PHONY: sync faraday preplab

##############################
#python3 -m unittest
tests test:
	nosetests --nologcapture tests

# when tests fail: pick your choice:
# turn log capture back on (remove --nologcapture)
# turn on actual output : run nose with -s or --nocapture
# pipe all in less : merge stderr in stdout
debugtest dbgtest:
	nosetests --nocapture tests 2>&1

test-sidecar:
	python3 -m unittest tests.test_sidecar

test-sidecar-local:
	python3 -m unittest tests.test_sidecar.Tests.local_nodes


.PHONY: tests test test-sidecar

########## sphinx
sphinx doc html:
	$(MAKE) -C sphinx html

sphinx-clean doc-clean html-clean:
	$(MAKE) -C sphinx clean

.PHONY: sphinx doc sphinx-clean doc-clean html html-clean

##########
pep8:
	git ls-files | grep '\.py$$' | grep -v '/conf.py$$' | xargs pep8

.PHONY: pep8
