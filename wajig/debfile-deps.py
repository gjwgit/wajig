#!/usr/bin/python3

# This file is part of wajig.  The copyright file is at debian/copyright.

import sys

import apt
from apt.debfile import DebPackage


def show_dependencies(debfile):

    install, remove, unauthenticated = debfile.required_changes
    prefix = "In order to allow installation of"

    if unauthenticated:
        # me not know what should happen here
        # awaiting bug report :)
        print("The following are UNAUTHENTICATED: ", end="")
        for package_name in unauthenticated:
            print(package_name + " ", end=" ")
        print()

    if remove:
        message = "{} {}, the following is to be REMOVED: "
        print(message.format(prefix, debfile.pkgname), end="")
        for package_name in remove:
            print(package_name + " ", end=" ")
        print()

    if install:
        message = "{} {}, the following is to be INSTALLED: "
        print(message.format(prefix, debfile.pkgname), end="")
        for package_name in install:
            print(package_name, end=" ")
        print()


def main(package):
    cache = apt.Cache()
    debfile = DebPackage(package, cache=cache)
    if debfile.check():
        show_dependencies(debfile)
        prompt = "Do you want to continue [Y/n]? "
        choice = input(prompt)
        if "y" == choice.lower() or not choice:
            try:
                cache.commit(apt.progress.text.AcquireProgress())
            except apt.cache.FetchFailedException as e:
                print(e)
        else:
            print("Abort.")


if __name__ == "__main__":
    main(sys.argv[1])
