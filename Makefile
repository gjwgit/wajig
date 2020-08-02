########################################################################
#
# Makefile for wajig command line. 
#
# Time-stamp: <Sunday 2020-08-02 12:47:10 AEST Graham Williams>
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
VER=3.2.2
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

INC_BASE    = $(HOME)/.local/share/make
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

  install	Install the current source version of $(APP) into ~/.local
  uninstall	Remove the local source installed version from ~/.local
  version	Update version from Makefile version number.
  pypi          Install onto PyPI for pip3 installation.

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


install: version $(APP).sh
	install -d  $(LIBDIR)/wajig $(BINDIR) $(MANDIR)
	cp $(APP)/*.py  $(LIBDIR)/wajig/
	mv $(LIBDIR)/wajig/__init__.py $(LIBDIR)
	cp $(APP).1  $(MANDIR)/
	install -D $(APP).sh $(BINDIR)/$(APP)

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

# dch -v 3.0.0 will update version in changelog and allow entry.
# Might be some way to do this purely command line.

deb: version $(APP).sh
	dpkg-buildpackage -us -uc
	mv ../$(APP)_$(VER)_all.deb .
	mv ../$(APP)_$(VER)_amd64.buildinfo .
	mv ../$(APP)_$(VER)_amd64.changes .
	mv ../$(APP)_$(VER).dsc .
	mv ../$(APP)_$(VER).tar.xz .

clean::
	rm -rf $(APP)/__pycache__

realclean::
	rm -f $(APP)_$(VER)*
