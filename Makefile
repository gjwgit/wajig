########################################################################
#
# Generic Makefile
#
# Time-stamp: <Sunday 2020-06-21 21:48:27 AEST Graham Williams>
#
# Copyright (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

APP=wajig
VER=3.0.2

INC_BASE    = $(HOME)/.local/share/make
INC_CLEAN   = $(INC_BASE)/clean.mk
INC_R       = $(INC_BASE)/r.mk
INC_KNITR   = $(INC_BASE)/knitr.mk
INC_PANDOC  = $(INC_BASE)/pandoc.mk
INC_GIT     = $(INC_BASE)/git.mk
INC_AZURE   = $(INC_BASE)/azure.mk
INC_LATEX   = $(INC_BASE)/latex.mk
INC_DOCKER  = $(INC_BASE)/docker.mk
INC_MLHUB   = $(INC_BASE)/mlhub.mk

ifneq ("$(wildcard $(INC_CLEAN))","")
  include $(INC_CLEAN)
endif
ifneq ("$(wildcard $(INC_PANDOC))","")
  include $(INC_PANDOC)
endif
ifneq ("$(wildcard $(INC_GIT))","")
  include $(INC_GIT)
endif
ifneq ("$(wildcard $(INC_LATEX))","")
  include $(INC_LATEX)
endif

define HELP
wajig:

  install	Install the current source version of wajig into ~/.local
  uninstall	Remove the local source installed version from ~/.local

  version	Update version from Makefile version number.
  deb		Create the debian package - not yet functional.
endef
export HELP

help::
	@echo "$$HELP"

# modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

DESTDIR ?= /home/$(USER)
PREFIX ?= /.local

LIBDIR = $(DESTDIR)$(PREFIX)/share/wajig
BINDIR = $(DESTDIR)$(PREFIX)/bin
MANDIR = $(DESTDIR)$(PREFIX)/share/man/man1

wajig.sh: wajig.sh.in
	sed -e 's|PREFIX|$(DESTDIR)$(PREFIX)|g' < $^ > $@

version:
	sed -i -e 's|^VERSION = ".*"|VERSION = "$(VER)"|' src/wajig.py
	sed -i -e 's|^APP = ".*"|APP = "$(APP)"|' src/wajig.py

install: wajig.sh
	install -d  $(LIBDIR) $(BINDIR) $(MANDIR)
	cp src/*.py  $(LIBDIR)/
	cp wajig.1  $(MANDIR)/
	install -D wajig.sh $(BINDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(BINDIR)/wajig

# dch -v 3.0.0 will update version in changelog and allow entry.
# Might be some way to do this purely command line.

deb: version wajig.sh
	dpkg-buildpackage -us -uc
	mv ../$(APP)_$(VER)_all.deb .
	mv ../$(APP)_$(VER)_amd64.buildinfo .
	mv ../$(APP)_$(VER)_amd64.changes .
	mv ../$(APP)_$(VER).dsc .
	mv ../$(APP)_$(VER).tar.xz .

clean::
	rm -rf src/__pycache__

realclean::
	rm -f $(APP)_$(VER)*
