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
import subprocess
import shlex


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
    cmd_install = "/usr/bin/sudo dpkg --install {}".format(packages)
    cmd_configure = "/usr/bin/sudo dpkg --configure --pending"

    if not os.path.exists("/usr/bin/sudo"):
        cmd_install = \
            "/bin/su --command 'dpkg --install {}'".format(packages)
        cmd_configure = \
            "/bin/su --command 'dpkg --configure --pending'"
    cmd_install = shlex.split(cmd_install)
    cmd_configure = shlex.split(cmd_configure)
    if subprocess.call(cmd_install):
        curdir = os.path.dirname(__file__)
        script = os.path.join(curdir, "debfile-deps.py")
        cmd = "/usr/bin/sudo {} {} {}"
        if not os.path.exists("/usr/bin/sudo"):
            cmd = "/bin/su --command '{} {} {}'"
        for package in package_list:
            cmd = cmd.format(sys.executable, script, package)
            cmd = shlex.split(cmd)
            subprocess.call(cmd)
    subprocess.call(cmd_configure)

if __name__ == "__main__":
    install(sys.argv[1:])
