#
# WAJIG - Debian Command Line System Administrator
#
# Copyright (c) Graham.Williams@togaware.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version. See the file LICENSE.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"Contains miscellaneous utilities."

import os
import sys
import commands

import apt

dist = str()  # stable, testing, unstable, ...
recommends_flag = None
fast = False  # Used for choosing 'apt-cache show' instead of the slower
              # 'aptitude show'; see debian/changelog for 2.0.50 why aptitude
              # was chosen as default.

def recommends():
    if recommends_flag is None:
        return ""
    elif recommends_flag is True:
        return "--install-recommends"
    else:
        return "--no-install-recommends"

def requires_no_args(command, args, test=False):
    if len(args) > 1:
        if not test:
            print(command.upper() + " requires no further arguments")
            finishup(1)
        return False
    return True


def requires_one_arg(command, args, message=False):
    if len(args) != 2:
        if message:  # checks if this is a unit test
            print(command.upper() + " requires " + message)
            finishup(1)
        return False
    return True


def requires_two_args(command, args, message=False):
    if len(args) != 3:
        if message:  # checks if this is a unit test
            print(command.upper() + " requires " + message)
            finishup(1)
        return False
    return True


def requires_opt_arg(command, args, message=False):
    if len(args) > 2:
        if message:  # checks if this is a unit test
            print(command.upper() + " has one optional arg: " + message)
            finishup(1)
        return False
    return True


def requires_args(command, args, required=False):
    if len(args) == 1:
        if required:  # checks if this is a unit test
            print("{0} requires {1}".format(command.upper(), required))
            finishup(1)
        return False
    return True


def requires_package(package, path, test=False):
    if not os.path.exists(path):
        if not test:
            print('This command depends on "' + package + '" being installed.')
            finishup(1)
        return False
    return True


def package_exists(package, test=False):
    cache = apt.Cache()
    try:
        cache[package]
        return True
    except KeyError as e:
        if not test:
            print(e[0])
            finishup(1)


def upgradable(distupgrade=False):
    "Checks if the system is upgradable."
    cache = apt.Cache()
    cache.upgrade(distupgrade)
    packages = [package.name for package in cache.get_changes()]
    return packages


def finishup(code=0):
    sys.exit(code)


def help(command):
    """Handles commands of the form 'wajig help install'."""
    try:
        command = command.replace("-", "")
        command = command.replace("_", "")
        help_text = eval("commands.{}.__doc__".format(command))
        print(help_text)
    except AttributeError:
        print(command.upper(), "is not a wajig command")


def local_changelog(package, tmp):
    "Retrieve Debian changelog from local installation."

    changelog = "/usr/share/doc/" + package + "/changelog.Debian.gz"
    changelog_native = "/usr/share/doc/" + package + "/changelog.gz"
    if os.path.exists(changelog):
        return "zcat {0} >> {1}".format(changelog, tmp)
    elif os.path.exists(changelog_native):
        return "zcat {0} >> {1}".format(changelog_native, tmp)
    else:
        print("Package", package, "is likely broken (changelog not found)!")


def extract_dependencies(package, dependency_type):
    """Produce all Dependencies of a particular type"""
    for dependency_list in package.candidate.get_dependencies(dependency_type):
        for dependency in dependency_list.or_dependencies:
            yield dependency.name


