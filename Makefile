########################################################################
#
# Makefile for wajig command line.
#
# Time-stamp: <Friday 2024-12-06 09:36:44 +1100 Graham Williams>
#
# Copyright (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

# App version numbers
#   Major release
#   Minor update
#   Trivial update or bug fix

APP=wajig
VER=4.1.3+2
DATE=$(shell date +%Y-%m-%d)

TAR_GZ = dist/$(APP)-$(VER).tar.gz

BASH_COMPLETION = $(APP)/bash_completion.d/$(APP).bash

SOURCE = setup.py			\
	 docs/README.md			\
	 setup.cfg			\
	 MANIFEST.in			\
	 LICENSE			\
	 $(APP)/constants.py		\
	 $(APP)/commands.py		\
	 $(APP)/debfile-deps.py		\
	 $(APP)/debfile.py			\
	 $(APP)/perform.py			\
	 $(APP)/shell.py			\
	 $(APP)/util.py			\
	 $(APP)/__init__.py		\
	 $(APP)/bash_completion.d/wajig.bash \

# Required modules.

INC_BASE    = support
INC_CLEAN   = $(INC_BASE)/clean.mk
INC_PANDOC  = $(INC_BASE)/pandoc.mk
INC_GIT     = $(INC_BASE)/git.mk
INC_LATEX   = $(INC_BASE)/latex.mk

ifneq ("$(wildcard $(INC_CLEAN))","")
  include $(INC_CLEAN)
endif
ifneq ("$(wildcard $(INC_R))","")
  include $(INC_R)
endif
ifneq ("$(wildcard $(INC_KNITR))","")
  include $(INC_KNITR)
endif
ifneq ("$(wildcard $(INC_PANDOC))","")
  include $(INC_PANDOC)
endif
ifneq ("$(wildcard $(INC_GIT))","")
  include $(INC_GIT)
endif
ifneq ("$(wildcard $(INC_AZURE))","")
  include $(INC_AZURE)
endif
ifneq ("$(wildcard $(INC_LATEX))","")
  include $(INC_LATEX)
endif
ifneq ("$(wildcard $(INC_PDF))","")
  include $(INC_PDF)
endif
ifneq ("$(wildcard $(INC_DOCKER))","")
  include $(INC_DOCKER)
endif
ifneq ("$(wildcard $(INC_MLHUB))","")
  include $(INC_MLHUB)
endif

define HELP
$(APP):

  install	NOT REQUIRED - already installed as 'pip install -e .'
  uninstall	Remove the local source installed version from ~/.local
  version	Update version from Makefile version number.

  pypi          Install onto PyPI for pip3 installation.
  deb           Build the debian package.

  snap		Build a snap.
  snapsh	Start a shell within multipass with the snap package.
  clean		Also performs snapcraft clean.

  access	Buld and copy deb to access.togaware.com
    azsync	Sync to deb@azure for building natively on Debian
    azbuild	Build the deb pacakge on the remote Debian server
    azget	Retrieve the built pacakge

  azstatus      VM status
  azup          Fire up the Azure server for Debian
  azdown	Shut down the Azure server.

endef
export HELP

help::
	@echo "$$HELP"

# modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

DESTDIR ?= /home/$(USER)
PREFIX ?= /.local

LIBDIR = $(DESTDIR)$(PREFIX)/share/$(APP)
BINDIR = $(DESTDIR)$(PREFIX)/bin
MANDIR = $(DESTDIR)$(PREFIX)/share/man/man1

$(APP).sh: $(APP).sh.in
	sed -e 's|PREFIX|$(DESTDIR)$(PREFIX)|g' < $^ > $@

.PHONY: .version
version:
	sed -i -e "s|^    version='.*'|    version='$(VER)'|" setup.py
	sed -i -e 's|^VERSION = ".*"|VERSION = "$(VER)"|' $(APP)/constants.py
	sed -i -e 's|^APP = ".*"|APP = "$(APP)"|' $(APP)/constants.py

# For testing a local install, install into
# ~/.local/share/wajig/wajig, with the __initi__.py in
# ~/.local/share/wajig, so it can call wajig.utils.

# 20230202 Use pip -e for local install now.

install: version $(APP).sh
	@echo "NOT REQUIRED. USE 'pip install -e .'"

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/$(APP).1
	rm -f $(BINDIR)/$(APP)

$(TAR_GZ): $(SOURCE)
	python3 setup.py sdist

.PHONY: tgz
tgz: $(TAR_GZ)

.PHONY: pypi
pypi: docs/README.md version tgz
	twine upload $(TAR_GZ)
	git tag v${VER} && git push --tags

# dch -v 3.0.0 will update version in changelog and allow entry.
# Might be some way to do this purely command line.

deb: version $(APP).sh
	sed -e 's|PREFIX|/usr|g' < $(APP).sh.in > $(APP).sh
	PREFIX=/usr dpkg-buildpackage -us -uc
	mv ../$(APP)_$(VER)_all.deb .
	mv ../$(APP)_$(VER)_amd64.buildinfo .
	mv ../$(APP)_$(VER)_amd64.changes .
	mv ../$(APP)_$(VER).dsc .
	mv ../$(APP)_$(VER).tar.xz .
	rm -f $(APP).sh

# 20230708 gjw az support has been removed.

azup:
	az vm start --resource-group deb --name deb

azdeb:
	rsync -avzh --delete ./ deb.australiacentral.cloudapp.azure.com:$(APP)/

azbuild: azdeb
	ssh deb.australiacentral.cloudapp.azure.com 'cd $(APP); make deb'

azget: azbuild
	scp deb.australiacentral.cloudapp.azure.com:$(APP)/$(APP)_$(VER)* .

azdown:
	az vm deallocate --resource-group deb --name deb

azstatus:
	az vm list --output table --show-details | egrep '(Name|----|deb)'

access: azget
	rsync --perms --chmod=u+rw,g+r,o+r $(APP)_$(VER)_all.deb togaware.com:apps/access/

# https://thecustomizewindows.com/2014/12/create-ubuntu-repository-ppa/

ppa: azget
	cd ppa
	dpkg-source -x ../$(APP)_$(VER).dsc
	cd $(APP)_$(VER)
	debuild -S -sa
	dput ppa:gjwkayon/ppa ../$(APP)_$(VER)_source.changes
.PHONY: snap
snap:
	snapcraft

snapsh:
	snapcraft prime --shell

clean::
	rm -rf $(APP)/__pycache__
	rm -f snap/*~
	snapcraft clean

realclean::
	rm -f $(APP)_$(VER)*

README.pdf: README.rst
	pandoc -V urlcolor=cyan -V geometry=a4paper -V lang=en-AU -V babel-lang=british --standalone --listings README.rst -o README.pdf
