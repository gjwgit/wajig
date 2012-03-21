# modified from a version found at:
# savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

LIBDIR = $(DESTDIR)/usr/share/wajig
BINDIR = $(DESTDIR)/usr/bin
MANDIR = $(DESTDIR)/usr/share/man/man1

clean:
	rm -rf src/__pycache__

install:
	mkdir -p  $(LIBDIR) $(HLPDIR) $(MANDIR)
	cp TUTORIAL $(LIBDIR)/
	cp src/*    $(LIBDIR)/
	cp wajig.1  $(MANDIR)/
	cp wajig.sh $(BINDIR)/wajig

uninstall:
	rm -rf $(LIBDIR)
	rm -f $(MANDIR)/wajig.1
	rm -f $(BINDIR)/wajig
	rm -f $(BCNDIR)/wajig
