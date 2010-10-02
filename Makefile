# 2010.10.02 this is modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

LIBDIR = $(DESTDIR)/usr/share/wajig
BINDIR = $(DESTDIR)/usr/bin
MANDIR = $(DESTDIR)/usr/share/man/man1
BCNDIR = $(DESTDIR)/etc/bash_completion.d

clean:
	rm -f *.py[co] */*.py[co] wajig.completion

install:
	mkdir -p $(LIBDIR) $(MANDIR)
	cp src/* $(LIBDIR)/
	cp manpages/*  $(MANDIR)/
	cp wajig.sh $(BINDIR)/wajig
	cp gjig.sh  $(BINDIR)/gjig
	./bash_completion.py
	cp wajig.completion $(BCNDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(MANDIR)/gjig.1
	rm -f $(BINDIR)/wajig
	rm -f $(BINDIR)/gjig
	rm -f $(BCNDIR)/wajig
