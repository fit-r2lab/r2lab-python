include Makefile.pypi

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

TMPDIR=/tmp/r2lab-dev-r2lab

# installing in $(TMPDIR) for testing
sync:
	@echo '===== '
	rsync -ai --relative $$(git ls-files) root@$(DEST):$(TMPDIR)/
	@echo '===== once copied, do the following as root on $(DEST)'
	@echo 'conda activate r2lab-dev-xxx && pip install -e $(TMPDIR)'

r2lab:
	$(MAKE) sync deployment=production

preplab:
	$(MAKE) sync deployment=preplab

.PHONY: sync r2lab preplab

##############################
tests: tests-unittest

tests-nosetest:
	nosetests --nologcapture tests

# when tests fail: pick your choice:
# turn log capture back on (remove --nologcapture)
# turn on actual output : run nose with -s or --nocapture
# pipe all in less : merge stderr in stdout
tests-debug:
	nosetests --nocapture tests 2>&1

tests-unittest:
	python3 -m unittest discover

test-sidecar:
	python3 -m unittest tests.test_sidecar

.PHONY: tests tests-unittest tests-debug tests-unittest test-sidecar

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
