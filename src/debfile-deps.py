#!/usr/bin/python3

# This file is part of wajig.  The copyright file is at debian/copyright.

import sys

import apt
from apt.debfile import DebPackage


def show_dependencies(deb):

    install, remove, unauthenticated = deb.required_changes
    prefix = "In order to allow installation of"

    if unauthenticated:
        # me not know what should happen here
        # awaiting bug report :)
        print ("The following are UNAUTHENTICATED: ", end="")
        for pkgname in unauthenticated:
            print(pkgname + " ", end=" ")
        print()

    if remove:
        print ("{} {}, the following is to be REMOVED: ".format(
                prefix, deb.pkgname), end="")
        for pkgname in remove:
            print(pkgname + " ", end=" ")
        print()

    if install:
        print ("{} {}, the following is to be INSTALLED: ".format(
                prefix, deb.pkgname), end="")
        for pkgname in install:
            print(pkgname, end=" ")
        print()


def main(package):
    cache = apt.Cache()
    deb = DebPackage(package, cache=cache)
    if deb.check():
        show_dependencies(deb)
        prompt = "Do you want to continue [Y/n]? "
        choice = input(prompt)
        if "y" == choice.lower() or not choice:
            cache.commit(apt.progress.text.AcquireProgress())
        else:
            print("Abort.")


if __name__ == "__main__":
    main(sys.argv[1])
