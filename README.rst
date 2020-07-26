wajig has evolved over many years and is based on our experiences of
installing and maintaining Debian and Ubunut based GNU/Linux systems.
It captures in a single command line tool all the tasks commonly
undertaken in managing GNU/Linux.

Wajig can be installed from any Debian/Ubuntu repository with:

```console
$ sudo apt install wajig
```

The latest version is also available from the PyPI repository:

```console
$ pip3 install wajig
```

Online documentation begins at <https://wajig.togaware.com> with the
bulk of the documentation at
<https://togaware.com/linux/survivor/wajig.html>. Source code is
maintained at <https://github.com/gjwgit/wajig>.

Dirk Eddelbuettel has been incredibly helpful in sponsoring wajig for
inclusion in Debian and in suggesting new commands. Tshepang
Lekhonkhobe was the maintainer for many years and contributed to a
significant cleanup of the code. Also, many thanks to other users of
wajig who have made suggestions over the years.

## Hacking

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

## howto release

* Ensure that version string on ``src/wajig.py`` matches that of
  latest changelog

* Ensure that debuild does not emit any lintian errors/warnings
