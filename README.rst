wajig has evolved over several years of using and maintaining Debian
systems.  It attempts to capture in a single command line tool various
things I commonly do that relate to managing the system. Many of the
commands supported by wajig have been gleemed from hints and gossip on
the mailing lists, and sometimes nuggets of useful information from
the documentation.

Online documentation is available at http://wajig.togaware.com.

Dirk Eddelbuettel has also been incredibly helpful in sponsoring wajig
for inclusion in Debian and in suggesting new commands. Also, many
thanks to other users of wajig who have made suggestions over the
years.

--> words by Graham Williams & updated/fixed by Tshepang Lekhonkhobe


hacking
-------

* Setup::

   wajig install devscripts debhelper
   debcheckout wajig
   cd wajig

* Build::

   debuild -us -uc

* Install::

   sudo debi

* Ensure that user-visible changes are mentioned in
  ``debian/changelog``; use ``/usr/bin/debchange`` from within the
  project root directory and do your changes there

howto release
-------------

* Run ``./test.py``; it's pitiful (5 tests), but that's better than
  nothing

* Ensure that version string on ``src/wajig.py`` matches that of
  latest changelog

* Ensure that debuild does not emit any lintian errors/warnings
