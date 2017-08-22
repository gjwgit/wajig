# modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

PREFIX ?= /usr

LIBDIR = $(DESTDIR)$(PREFIX)/share/wajig
BINDIR = $(DESTDIR)$(PREFIX)/bin
MANDIR = $(DESTDIR)$(PREFIX)/share/man/man1

wajig:
	sed -e 's|PREFIX|$(PREFIX)|g' < wajig.sh.in > wajig.sh

clean:
	rm -rf src/__pycache__

install: wajig
	install -d  $(LIBDIR) $(MANDIR) $(CMPDIR)
	cp src/*.py  $(LIBDIR)/
	cp wajig.1  $(MANDIR)/
	install -D wajig.sh $(BINDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(BINDIR)/wajig
