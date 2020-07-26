#!/usr/bin/python3

# This file is part of wajig.  The copyright file is at debian/copyright.

"""
Primitive (no error handling) script to install a DEB file and its
dependencies. It can be called via wajig or directly:

$ wajig install <DEB file>
$ python3 /path/to/debfile.py <DEB file>
"""

import os
import sys
import wajig.perform as perform


def install(package_list):
    """Some gymnastics to try install local DEB files"""

    non_existent = list()
    for package in package_list:
        if not os.path.exists(package):
            non_existent.append(package)
    if non_existent:
        print("File(s) not found: " + " ".join(non_existent))
        return 1

    packages = " ".join(package_list)
    cmd_install = "dpkg --install {}".format(packages)
    cmd_configure = "dpkg --configure --pending"

    if perform.execute(cmd_install, root=True):
        curdir = os.path.dirname(__file__)
        script = os.path.join(curdir, "debfile-deps.py")
        for package in package_list:
            command = "{} {} {}".format(sys.executable, script, package)
            perform.execute(command, root=True)
    perform.execute(cmd_configure, root=True)

if __name__ == "__main__":
    install(sys.argv[1:])
