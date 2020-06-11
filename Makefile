########################################################################
#
# Generic Makefile
#
# Time-stamp: <Thursday 2020-06-11 17:17:55 AEST Graham Williams>
#
# Copyright (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

APP=wajig
VER=3.0.0

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
ifneq ("$(wildcard $(INC_DOCKER))","")
  include $(INC_DOCKER)
endif
ifneq ("$(wildcard $(INC_MLHUB))","")
  include $(INC_MLHUB)
endif

define HELP
wajig:

  install	Install the current source version of wajig into ~/.local
  uninstall	Remove the local source installed version from ~/.local

  wajig		Create wajig.sh. Update version from Makefile version number.
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

wajig:
	sed -e 's|PREFIX|$(DESTDIR)$(PREFIX)|g' < wajig.sh.in > wajig.sh
	sed -i -e 's|^VERSION = ".*"|VERSION = "$(VER)"|' src/wajig.py

install: wajig
	install -d  $(LIBDIR) $(BINDIR) $(MANDIR)
	cp src/*.py  $(LIBDIR)/
	cp wajig.1  $(MANDIR)/
	install -D wajig.sh $(BINDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(BINDIR)/wajig

clean::
	rm -rf src/__pycache__

