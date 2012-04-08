# This file is part of wajig.  The copyright file is at debian/copyright.

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


def package_exists(cache, package, test=False, ignore_virtual_packages=False):
    try:
        if cache.is_virtual_package(package) and not ignore_virtual_packages:
            return cache.get_providing_packages(package)[0]
        return cache[package]
    except KeyError as error:
        if not test:
            print(error.args[0])
            sys.exit(1)


def upgradable(distupgrade=False, get_names_only=True):
    "Checks if the system is upgradable."
    cache = apt.Cache()
    cache.upgrade(distupgrade)
    if get_names_only:
        packages = [package.name for package in cache.get_changes()]
    else:
        packages = [package for package in cache.get_changes()]
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


def extract_dependencies(package, dependency_type="Depends"):
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


def do_describe_new(verbose=False):
    """Report on packages that are newly available."""
    new_packages = upgradable()
    if new_packages:
        do_describe(new_packages, verbose)
    else:
        print("No new packages")


def show_package_versions():
    packages = upgradable(get_names_only=False)
    if packages:
        print("{:<24} {:<24} {}".format("Package", "Available", "Installed"))
        print("="*24 + "-" + "="*24 + "-" + "="*24)
        for package in sorted(packages):
            print("{:<24} {:<24} {}".format(package.name,
                package.candidate.version, package.installed.version))
    return packages


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
    results = perform.execute(command, root=needsudo, pipe=True)
    if results:
        lines = results.readlines()
        if lines:
            return perform.execute(command, root=needsudo, pipe=pipe)
    else:
        sys.exit(1)


def do_update(simulate=False):
    if not perform.execute("apt-get update", root=True):
        if not simulate:
            changes.update_available()
            print("There are {} new upgrades".format(changes.count_upgrades()))


def get_deps_recursively(cache, package, packages):
    if not package in packages:
        packages.append(package)
    for package_name in \
        extract_dependencies(package_exists(cache, package)):
        if package_name not in packages:
            packages.append(package_name)
            get_deps_recursively(cache, package_name, packages)
    return packages


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
