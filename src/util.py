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
import tempfile
import re

import apt
import apt_pkg

import changes
import perform


def requires_package(package, path, test=False):
    if not os.path.exists(path):
        if not test:
            print('This command depends on "' + package + '" being installed.')
            sys.exit(1)
        return False
    return True


def package_exists(cache, package, test=False):
    try:
        return cache[package]
    except KeyError as error:
        if not test:
            print(error.args[0])
            sys.exit(1)


def upgradable(distupgrade=False):
    "Checks if the system is upgradable."
    cache = apt.Cache()
    cache.upgrade(distupgrade)
    packages = [package.name for package in cache.get_changes()]
    return packages


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


def do_describe(packages, verbose=False):
    """Display package description(s)."""

    package_files = [package for package in packages
                     if package.endswith(".deb")]
    package_names = [package for package in packages
                     if not package.endswith(".deb")]
    if package_files:
        for package_file in package_files:
            perform.execute("dpkg-deb --info " + package_file)
            print("="*72)
            sys.stdout.flush()

    if package_names:
        packages = package_names
    else:
        return

    if not packages:
        print("No packages found from those known to be available/installed.")
    else:
        packageversions = list()
        cache = apt.cache.Cache()
        for package in packages:
            try:
                package = cache[package]
            except KeyError as e:
                print(str(e).strip('"'))
                return 1
            packageversion = package.installed
            if not packageversion:  # if package is not installed...
                packageversion = package.candidate
            packageversions.append((package.shortname, packageversion.summary,
                                packageversion.description))
        packageversions = set(packageversions)
        if verbose:
            for packageversion in packageversions:
                print("{}: {}\n{}\n".format(packageversion[0],
                                            packageversion[1],
                                            packageversion[2]))
        else:
            print("{0:24} {1}".format("Package", "Description"))
            print("="*24 + "-" + "="*51)
            for packageversion in packageversions:
                print("%-24s %s" % (packageversion[0], packageversion[1]))


def do_describe_new(install=False, verbose=False):
    """Report on packages that are newly available."""
    new_packages = changes.get_new_available()
    if new_packages:
        util.do_describe(new_packages, verbose)
        if install:
            print("="*76)
            do_install(new_packages)
    else:
        print("No new packages")


def ping_host(hostname):
    """Check if network host is reachable."""
    # Check if we can talk to the HOST
    command = "fping {} 2>/dev/null >/dev/null".format(hostname)
    if perform.execute(command):
        print("Could not contact the Debian server at " + hostname)
        print("Perhaps it is down or you are not connected to the network.")
        return False
    return True


def do_newupgrades(install, yes, noauth):
    """Display packages that are newly upgraded."""

    # Load the dictionaries from file then list each one and it's version
    new_upgrades = changes.get_new_upgrades()
    if len(new_upgrades) == 0:
        print("No new upgrades")
    else:
        print("%-24s %-24s %s" % ("Package", "Available", "Installed"))
        print("="*24 + "-" + "="*24 + "-" + "="*24)
        new_upgrades.sort()
        for i in range(0, len(new_upgrades)):
            print("%-24s %-24s %-24s" % (new_upgrades[i], \
                            changes.get_available_version(new_upgrades[i]), \
                            changes.get_installed_version(new_upgrades[i])))
        if install:
            print("="*74)
            command = "apt-get install {} {}" + " ".join(new_upgrades)
            command = command.format(yes, noauth)
            perform.execute(command, root=True)


def display_sys_docs(package, filenames):
    """This services README and NEWS commands"""
    docpath = os.path.join("/usr/share/doc", package)
    if not os.path.exists(docpath):
        if package_exists(apt.Cache(), package):
            print("'{}' is not installed".format(package))
        return
    found = False
    for filename in filenames:
        path = os.path.join(docpath, filename)
        cat = "cat"
        if not os.path.exists(path):
            path += ".gz"
            cat = "zcat"
        if os.path.exists(path):
            found = True
            print("{0:=^72}".format(" {0} ".format(filename)))
            sys.stdout.flush()
            perform.execute(cat + " " + path)
    if not found:
        print("File not found")


def do_status(packages, snapshot=False):
    """List status of the packages identified.

    Arguments:
    packages    List the version of installed packages
    snapshot    Whether a snapshot is required (affects output format)
    """

    if not snapshot:
        print("%-23s %-15s %-15s %-15s %s" % \
              ("Package", "Installed", "Previous", "Now", "State"))
        print("="*23 + "-" + "="*15 + "-" + "="*15 + "-" + "="*15 + "-" + "="*5)
        sys.stdout.flush()
    #
    # Get status.  Previously used dpkg --list but this truncates package
    # names to 16 characters :-(. Perhaps should now also remove the DS
    # column as that was the "ii" thing from dpkg --list.  It is now
    # "install" or "deinstall" from dpkg --get-selections.
    #
    #   command = "dpkg --list | " +\
    #             "awk '{print $2,$1}' | " +\
    #
    # Generate a temporary file of installed packages.
    #
    ifile = tempfile.mkstemp()[1]
    #
    # Using langC=TRUE here makes it work for other LANG, e.g.,
    # LANG=ru_RU.koi8r. Seems that the sorting is the key problem. To
    # test, try:
    #
    #   $ wajign status | wc -l
    #   1762
    #   $ LANG=ru_RU.koi8r wajign status | wc -l
    #   1762
    #
    # But now set it to False (the default):
    #
    #   $ LANG=ru_RU.koi8r wajign status | wc -l
    #   1449
    #
    # See Bug#288852 and Bug#119899.
    #
    perform.execute(changes.gen_installed_command_str() + " > " + ifile,
                    langC=True)
    #
    # Build the command to list the status of installed packages.
    #
    available_file = changes.available_file
    previous_file = changes.previous_file

    command = "dpkg --get-selections | join - " + ifile + " | " +\
              "join -a 1 - " + previous_file + " | " +\
              "awk 'NF==3 {print $0, \"N/A\"; next}{print}' | " +\
              "join -a 1 - " + available_file + " | " +\
              "awk 'NF==4 {print $0, \"N/A\"; next}{print}' | "
    if len(packages) > 0:
        # Use grep, not egrep, otherwise g++ gets lost, for example!
        command = command + "grep '^\($"
        for i in packages:
            command = command + " \|" + i
        command = command + " \)' |"

    command = command +\
              "awk '{printf(\"%-20s\\t%-15s\\t%-15s\\t%-15s\\t%-2s\\n\", " +\
              "$1, $3, $4, $5, $2)}'"
    if snapshot:
        fobj = perform.execute(command, pipe=True)
        for l in fobj:
            print("=".join(l.split()[0:2]))
    else:
        perform.execute(command, langC=True)
    #
    # Check whether the package is not in the installed list, and if not
    # list its status appropriately.
    #
    for i in packages:
        if perform.execute("egrep '^" + i + " ' " + ifile + " >/dev/null"):
            # Package is not installed.
            command = \
              "join -a 2 " + previous_file + " " + available_file + " | " +\
              "awk 'NF==2 {print $1, \"N/A\", $2; next}{print}' | " +\
              "egrep '^" + i + " '"
            command = command +\
              " | awk '{printf(\"%-20s\\t%-15s\\t%-15s\\t%-15s\\n\", " +\
              "$1, \"N/A\", $2, $3)}'"
            perform.execute(command, langC=True)

    # Tidy up - remove the "installed file"
    if os.path.exists(ifile):
        os.remove(ifile)


def do_listnames(pattern=False, pipe=False):

    # If user can't access /etc/apt/sources.list then must do this with
    # sudo or else most packages will not be found.
    needsudo = not os.access("/etc/apt/sources.list", os.R_OK)
    if pattern:
        command = "apt-cache pkgnames | grep -- " + pattern \
                + " | sort -k 1b,1"
    else:
        command = "apt-cache pkgnames | sort -k 1b,1"
    # Start fix for Bug #292581 - pre-run command to check for no output
    results = perform.execute(command, root=needsudo, pipe=True).readlines()
    if results:
        return perform.execute(command, root=needsudo, pipe=pipe)


def do_update():
    if not perform.execute("apt-get update", root=True):
        changes.update_available()
        print("There are " + changes.count_upgrades() + " new upgrades")


def get_deps_recursively(cache, package, packageslist):
    if not package in packageslist:
        packageslist.append(package)
    try:
        for package_name in extract_dependencies(cache[package], "Depends"):
            if package_name not in packageslist:
                packageslist.append(package_name)
                get_deps_recursively(cache, package_name, packageslist)
    except KeyError as error:
        print(error.args[0])  # "package does not exist in cache"
        sys.exit(1)
    return packageslist

def consolidate_package_names(args):
    packages = list()
    filelist = list()
    if args.fileinput:
        for path in args.packages:
            if os.path.isfile(path):
                with open(path) as f:
                    packages.extend(f.read().split())
                    filelist.append(path)
    packages.extend(args.packages)
    # filenames are not package names; this feels like a hack
    for filename in filelist:
        packages.remove(filename)
    return set(packages)

def sizes(packages=None, size=0):
    status = apt_pkg.TagFile(open("/var/lib/dpkg/status", "r"))
    size_list = dict()
    status_list = dict()

    for section in status:
        package_name   = section.get("Package")
        package_size   = section.get("Installed-Size")
        package_status = re.split(" ", section.get("Status"))[2]
        if package_size and int(package_size) > size:
            if package_name not in size_list:
                size_list[package_name] = package_size
                status_list[package_name] = package_status

    packages = list(size_list)
    packages.sort(key=lambda x: int(size_list[x]))  # sort by size

    if packages:
        print("{:<33} {:^10} {:>12}".format("Package", "Size (KB)", "Status"))
        print("{}-{}-{}".format("="*33, "="*10, "="*12))
        for package in packages:
            message = "{:<33} {:^10} {:>12}".format(package,
                       format(int(size_list[package]), ',d'),
                       status_list[package])
            print(message)
    else:
        print("No packages of >10MB size found")

