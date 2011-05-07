# modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

LIBDIR = $(DESTDIR)/usr/share/wajig
HLPDIR = $(LIBDIR)/help
BINDIR = $(DESTDIR)/usr/bin
MANDIR = $(DESTDIR)/usr/share/man/man1
BCNDIR = $(DESTDIR)/etc/bash_completion.d

clean:
	rm -f *.py[co] */*.py[co]

install:
	mkdir -p  $(LIBDIR) $(HLPDIR) $(MANDIR)
	cp src/*  $(LIBDIR)/
	cp help/* $(HLPDIR)/
	cp wajig.1  $(MANDIR)/
	cp wajig.sh $(BINDIR)/wajig
	cp wajig.completion $(BCNDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(BINDIR)/wajig
	rm -f $(BCNDIR)/wajig
