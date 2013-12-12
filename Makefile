# modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

LIBDIR = $(DESTDIR)/usr/share/wajig
BINDIR = $(DESTDIR)/usr/bin
MANDIR = $(DESTDIR)/usr/share/man/man1
CMPDIR = $(DESTDIR)/etc/bash_completion.d

clean:
	rm -rf src/__pycache__

install:
	install -d  $(LIBDIR) $(MANDIR) $(CMPDIR)
	cp src/*.py  $(LIBDIR)/
	cp TUTORIAL $(LIBDIR)/
	cp wajig.1  $(MANDIR)/
	install -D wajig.sh $(BINDIR)/wajig
	cp bash-completion $(CMPDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(BINDIR)/wajig
	rm -f $(CMPDIR)/wajig
