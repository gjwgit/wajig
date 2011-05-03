#!/usr/bin/python3
# This file is part of wajig.  The copyright file is at debian/copyright.

"""
Primitive (no error handling) script to install a DEB file and its
dependencies. It can be called via waig or directly:

$ wajig install <DEB file>
OR
$ python3 /path/to/debfile.py <DEB file>

"""

import os
import sys
import shlex
import subprocess

import apt
from apt.debfile import DebPackage


def show_dependencies(deb):

    install, remove, unauthenticated = deb.required_changes

    if unauthenticated:
        print ("The following package(s) are UNAUTHENTICATED: ", end="")
        for pkgname in unauthenticated:
            print(pkgname + " ", end=' ')
        print()

    if remove:
        print ("The following packages are to be REMOVED: ", end="")
        for pkgname in remove:
            print(pkgname + " ", end=' ')
        print()

    if install:
        print ("The following packages are to be INSTALLED: ", end="")
        for pkgname in install:
            print(pkgname, end=' ')
        print()

if __name__ == "__main__":
    for package in sys.argv[1:]:
        if not os.path.exists(package):
            print(package + " not found!")
            break
        cache = apt.Cache()
        deb = DebPackage(package, cache=cache)
        deb.check()
        show_dependencies(deb)
        choice = input("Do you want to continue [Y/n]? ")
        if "y" == choice.lower() or not choice:
            cache.commit(apt.progress.text.AcquireProgress())
            deb.install()
        else:
            print("Abort.")
