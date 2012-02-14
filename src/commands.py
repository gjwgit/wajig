#
# WAJIG - Debian Package Management Front End
#
# Implementation of all commands
#
# Copyright (c) Graham.Williams@togaware.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
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

import os
import re
import sys
import tempfile
import signal

import apt_pkg
import apt

# wajig modules
import changes
import perform
import util
import debfile

# When writing to a pipe where there is no reader (e.g., when
# output is directed to head or to less and the user exists from less
# before reading all output) the SIGPIPE signal is generated. Capture
# the signal and hadle it with the default handler.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

verbose = 0
available_file = changes.available_file
previous_file  = changes.previous_file


def set_verbosity_level(new_level):
    global verbose
    verbose = new_level


def ping_host(hostname):
    "Check if host is reachable."

    # Check if fping is installed.
    if perform.execute("fping localhost 2>/dev/null >/dev/null",
                       display=False) != 0:
        print("fping was not found. " +\
              "Consider installing the package fping.\n")

    # Check if we can talk to the HOST
    elif perform.execute("fping " + hostname + " 2>/dev/null >/dev/null",
                         display=False) != 0:
        print("Could not contact the Debian server at " + hostname\
        + """
             Perhaps it is down or you are not connected to the network.
             JIG will continue to try to get the information required.""")
    else:
        return True  # host found


def get_available(command="dumpavail"):
    "Return an apt_pkg object that represents the parsed list of packages."

    # This originally ran the apt-cache command as a pipe to
    # TagFile as in:
    #  command = "apt-cache dumpavail"
    #  packages_pipe = perform.execute(command, pipe=True)
    #  avail = apt_pkg.TagFile(packages_pipe)
    #
    # But as in Bug#366678 TagFile no longer works in a pipe
    # because of changes to apt_pkg by Michael Vogt. He supplied
    # suggested fixes, but they were not tested and I've not had
    # a chance to understand the new APT package for Python. So put
    # the apt-cache dump into a file and then use that file here.

    # 090501 Note that using "apt-cache dumpavail" misses packages
    # that are installed but are no longer available. So why not
    # append /var/lib/dpkg/status to be more comprehensive? Would
    # repeats be an issue? Closes Bug#432266

    tmpcache = tempfile.mkstemp()[1]
    perform.execute("apt-cache dumpavail > " + tmpcache)
    perform.execute("cat /var/lib/dpkg/status >> " + tmpcache)  # 090501 fix
    avail = apt_pkg.TagFile(open(tmpcache))
    if os.path.exists(tmpcache):
        os.remove(tmpcache)
    return avail


def getdeps(deptype, pkg, otherpkg):
    li = list()
    name = otherpkg.shortname
    otherpkg = otherpkg.candidate
    for deplist in otherpkg.get_dependencies(deptype):
        for dep in deplist.or_dependencies:
            if dep.name == pkg.shortname:
                li.append(name)
    return li


def do_dependents(pkg):
    cache = apt.cache.Cache()
    try:
        pkg = cache[pkg]
    except KeyError as e:
        print(str(e).strip('"'))
        return

    dependents = dict()
    depends = list()
    recommends = list()
    suggests = list()
    replaces = list()
    enhances = list()
    for key in cache.keys():
        otherpkg = cache[key]
        depends.append(getdeps("Depends", pkg, otherpkg))
        recommends.append(getdeps("Recommends", pkg, otherpkg))
        suggests.append(getdeps("Suggests", pkg, otherpkg))
        replaces.append(getdeps("Replaces", pkg, otherpkg))
        enhances.append(getdeps("Enhances", pkg, otherpkg))

    dependents["Depends"] = depends
    dependents["Recommends"] = recommends
    dependents["Suggests"] = suggests
    dependents["Replaces"] = replaces
    dependents["Enhances"] = enhances
    for deptype, deps in dependents.items():
        deps_output = list()
        for match in deps:
            if match:
                for item in match:
                    deps_output.append(item)
        if deps_output:
            print(deptype.upper(), end=": ")
            print(" ".join(deps_output))


def do_describe(packages):
    """Display package description(s)."""

    package_files = [pkg for pkg in packages if pkg.endswith(".deb")]
    package_names = [pkg for pkg in packages if not pkg.endswith(".deb")]
    if package_files:
        for package_file in package_files:
            perform.execute("dpkg-deb --info " + package_file)
            print("="*72)
            sys.stdout.flush()

    if package_names:
        packages = package_names
    else:
        return

    global verbose
    if (verbose > 2):
        verbose = 2
    if (not packages) and (verbose < 2):
        print("No packages found from those known to be available/installed.")
    elif verbose == 2:
        package_names = util.concat(set(packages))
        cmd = "apt-cache" if util.fast else "aptitude"
        perform.execute("{} show {}".format(cmd, package_names))

    elif verbose in (0, 1):
        pkgversions = list()
        cache = apt.cache.Cache()
        for pkg in packages:
            try:
                pkg = cache[pkg]
            except KeyError as e:
                print(str(e).strip('"'))
                return 1
            pkgversion = pkg.installed
            if not pkgversion:  # if package is not installed...
                pkgversion = pkg.candidate
            pkgversions.append((pkg.shortname, pkgversion.summary,
                                pkgversion.description))
        pkgversions = set(pkgversions)
        if verbose == 0:
            print("{0:24} {1}".format("Package", "Description"))
            print("="*24 + "-" + "="*51)
            for pkgversion in pkgversions:
                print("%-24s %s" % (pkgversion[0], pkgversion[1]))
        else:
            for pkgversion in pkgversions:
                print("{}: {}\n{}\n".format(pkgversion[0],
                                            pkgversion[1],
                                            pkgversion[2]))


def do_describe_new(install=False):
    "Report on packages that are newly available."

    #
    # Describe each new package.
    #
    new_pkgs = changes.get_new_available()
    if len(new_pkgs) == 0:
        print("No new packages")
    else:
        do_describe(new_pkgs)
        if install:
            print("="*76)
            do_install(new_pkgs)


def do_download(packages):
    "Download packages without installing them."

    command = "apt-get --download-only install " + util.concat(packages)
    perform.execute(command, root=1)


def do_force(packages):
    """Force the installation of a package.

    This is useful when there is a conflict of the same file from
    multiple packages or when a dependency is not installed for
    whatever reason.
    """
    #
    # The basic function is to force install the package using dpkg.
    #
    command = "dpkg --install --force overwrite --force depends "
    archives = "/var/cache/apt/archives/"
    #
    # For a .deb file we simply force install it.
    #
    if re.match(".*\.deb$", packages[0]):
        for pkg in packages:
            if os.path.exists(pkg):
                command += "'" + pkg + "' "
            elif os.path.exists(archives + pkg):
                command += "'" + archives + pkg + "' "
            else:
                print("""File `%s' not found.
              Searched current directory and %s.
              Please confirm the location and try again.""" % (pkg, archives))
                return()
    else:
        #
        # Package names rather than a specific deb package archive
        # is expected.
        #
        for pkg in packages:
            #
            # Identify the latest version of the package available in
            # the download archive, if there is any there.
            #
            lscmd = "/bin/ls " + archives
            lscmd += " | egrep '^" + pkg + "_' | sort -k 1b,1 | tail -n -1"
            matches = perform.execute(lscmd, pipe=True)
            debpkg = matches.readline().strip()
            #
            # If the package was not perfound then download it before
            # it is force installed.
            #
            if not debpkg:
                dlcmd = "apt-get --quiet=2 --reinstall --download-only "
                dlcmd += "install '" + pkg + "'"
                perform.execute(dlcmd, root=1)
                matches = perform.execute(lscmd, pipe=True)
                debpkg = matches.readline().strip()
            #
            # Force install the package from the download archive.
            #
            command += "'" + archives + debpkg + "' "
    #
    # The command has been built.  Now execute it.
    #
    perform.execute(command, root=1)


def do_hold(packages):
    "Place packages on hold (so they will not be upgraded)."

    for p in packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then!
        command = "echo \"" + p + " hold\" | dpkg --set-selections"
        perform.execute(command, root=1)
    print("The following packages are on hold:")
    perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")


def do_install(packages, yes="", noauth="", dist=""):
    "Install packages."

    #
    # Currently we use the first argument to determine the type of all
    # of the rest. Perhaps we should look at each one in turn?
    #

    #
    # Handle URLs first. We don't do anything smart.  Simply download
    # the .deb file and install it.  If it fails then don't attempt to
    # recover.  The user can do a wget themselves and install the
    # resulting .deb if they need to.
    #
    # Currently only a single URL is allowed. Should this be generalised?
    #

    # reading packages from stdin
    if len(packages) == 1 and packages[0] == "-":
        stripped = [x.strip() for x in sys.stdin.readlines()]
        joined = str.join(stripped)
        packages = joined.split()

    # reading packages from a file
    elif len(packages) == 2 and packages[0] == "-f":
        stripped = [x.strip() for x in open(packages[1]).readlines()]
        joined = str.join(stripped)
        packages = str.split(joined)

    # check if a specific web location was specified
    if re.match("(http|ftp)://", packages[0]) \
       and util.requires_package("wget", "/usr/bin/wget"):
        if len(packages) > 1:
            print("install URL allows only one URL, not " +\
                  str(len(packages)))
            sys.exit(1)
        tmpdeb = tempfile.mkstemp()[1] + ".deb"
        command = "wget --output-document=" + tmpdeb + " " + packages[0]
        if not perform.execute(command):
            command = "dpkg --install " + tmpdeb
            perform.execute(command, root=1)
            if os.path.exists(tmpdeb):
                os.remove(tmpdeb)
        else:
            print("The location " + packages[0] +\
                  " was not found. Check and try again.")

    # check if DEB files were specified
    elif re.match(".*\.deb$", packages[0]):
        debfile.install(set(packages))
    #
    # Check if a "/+" is in a package name then use the following distribution
    # for all packages! We might not want this previsely if there are multiple
    # packages listed and only one has the /+ notation. So do it only for the
    # specified one. I have introduced this notation myself, extending
    # the apt-get "/" notation. "+" by itself won't work since "+" can
    # appear in a package name, and it is okay if a distribution name starts
    # with "+" since you just include two "+"'s then.
    #
    # TODO
    #
    # Currently only do this for the first package........
    #
#     elif re.match(".*/+.*", packages[0]):
#         print "HI"
#         (packages[0], release) = re.compile(r'/\+').split(packages[0])
#       command = "apt-get --target-release %s install %s" %\
#                   (release, util.concat(packages))
#       perform.execute(command, root=1)
    else:
        rec = util.recommends()
        if dist:
            dist = "--target-release " + dist
        cmd = "apt-get {0} {1} {2} {3} install {4}"
        cmd = cmd.format(yes, noauth, rec, dist, util.concat(packages))
        perform.execute(cmd, root=True)


def do_install_suggest(packages, yes, noauth):
    "Install packages suggested by the listed packages."

    # If reading from standard input, generate the list of packages.
    if len(packages) == 1 and packages[0] == "-":
        stripped = [x.strip() for x in sys.stdin.readlines()]
        joined = str.join(stripped)
        packages = joined.split()

    # For each package obtain the list of suggested packages
    suggest_list = ""

    # Obtain the details of each available package.
    avail = get_available()

    # Check for information in the Available list
    for section in avail:
        if section.get("Package") in packages:
            sug = section.get("Suggests")
            if sug:
                suggest_list = "{0} {1}".format(suggest_list, sug)

    # Remove version information
    suggest_list = re.sub('\([^)]*\)', '', suggest_list)

    # Remove the commas from the list
    suggest_list = re.sub(',', '', suggest_list)

    # Deal with alternatives.
    # For now simply ignore all alternatives.
    # Should prompt user to select one?
    suggest_list = re.sub(' *[a-z0-9-]* *\| *[a-z0-9-]* *', ' ', suggest_list)

    # Remove duplicates
    suggest_list = suggest_list + " "
    for i in suggest_list.split():
        suggest_list = i + " " + re.sub(" " + i + " ", ' ', suggest_list)

    perform.execute("apt-get {0} {1} {2} --show-upgraded install {3} {4}".\
                     format(util.recommends(), yes, noauth, \
                     util.concat(packages), suggest_list),
                     root=True)


def do_listsections():
    cache = apt.cache.Cache()
    sections = list()
    for pkg in cache.keys():
        pkg = cache[pkg]
        sections.append(pkg.section)
    sections = set(sections)
    for section in sections:
        print(section)


def do_listsection(section):
    cache = apt.cache.Cache()
    for pkg in cache.keys():
        pkg = cache[pkg]
        if(pkg.section == section):
            print(pkg.name)


def do_listinstalled(pattern):
    "Display a list of installed packages."
    command = "dpkg --get-selections | awk '$2 ~/^install$/ {print $1}'"
    if len(pattern) == 1:
        command = command + " | grep -- " + pattern[0] + " | sort -k 1b,1"
    perform.execute(command)


def do_listnames(pattern, pipe=False):
    "Print list of known package names."

    # If user can't access /etc/apt/sources.list then must do this with
    # sudo or else most packages will not be found.
    needsudo = not os.access("/etc/apt/sources.list", os.R_OK)
    if len(pattern) == 0:
        command = "apt-cache pkgnames | sort -k 1b,1"
    else:
        command = "apt-cache pkgnames | grep -- " + pattern[0] \
                + " | sort -k 1b,1"
    # Start fix for Bug #292581 - pre-run command to check for no output
    results = perform.execute(command, root=needsudo, pipe=True).readlines()
    if len(results) == 0:
        sys.exit(1)
    # End fix for Bug #292581
    return perform.execute(command, root=needsudo, pipe=pipe)


def do_listscripts(pkg):
    scripts = ["preinst", "postinst", "prerm", "postrm"]
    if re.match(".*\.deb$", pkg):
        command = "ar p " + pkg + " control.tar.gz | tar ztvf -"
        pkgScripts = perform.execute(command, pipe=True).readlines()
        for script in scripts:
            if "./" + script in "".join(pkgScripts):
                nlen = (72 - len(script)) / 2
                print(">"*nlen, script, "<"*nlen)
                command = "ar p " + pkg + " control.tar.gz |" +\
                          "tar zxvf - -O ./" + script +\
                          " 2>/dev/null"
                perform.execute(command)
    else:
        root = "/var/lib/dpkg/info/"
        for script in scripts:
            fname = root + pkg + "." + script
            if os.path.exists(fname):
                nlen = (72 - len(script))/2
                print(">"*nlen, script, "<"*nlen)
                perform.execute("cat " + fname)


def do_new():
    "Report on packages that are newly available."

    print("%-24s %s" % ("Package", "Available"))
    print("="*24 + "-" + "="*16)
    #
    # List each package and it's version
    #
    new_pkgs = changes.get_new_available()
    new_pkgs.sort()
    for i in range(0, len(new_pkgs)):
        print("%-24s %s" % (new_pkgs[i],
            changes.get_available_version(new_pkgs[i])))


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


def do_changelog(package):
    """Display Debian changelog.

    network on:
         changelog - if there's newer entries, display them
      -v changelog - if there's newer entries, display them, and proceed to
                     display complete local changelog

    network off:
         changelog - if there's newer entries, mention failure to retrieve
      -v changelog - if there's newer entries, mention failure to retrieve, and
                     proceed to display complete local changelog
    """

    changelog = "{:=^79}\n".format(" {} ".format(package))  # header

    pkg = apt.Cache()[package]
    try:
        changelog += pkg.get_changelog()
    except AttributeError as e:
        # This is caught so as to avoid an ugly python-apt trace; it's a bug
        # that surfaces when:
        # 1. The package is not available in the default Debian suite
        # 2. The suite the package belongs to is set to a pin of < 0
        print("If this package is not on your default Debian suite, " \
              "ensure that it's APT pinning isn't less than 0.")
        return
    help_message = "\nTo display the local changelog, run:\n" \
                   "wajig --verbose changelog " + package
    if "Failed to download the list of changes" in changelog:
        if not verbose:
            changelog += help_message
        else:
            changelog += "\n"
    elif changelog.endswith("The list of changes is not available"):
        changelog += ".\nYou are likely running the latest version."
        if not verbose:
            changelog += help_message
    if not verbose:
        print(changelog)
    else:
        tmp = tempfile.mkstemp()[1]
        with open(tmp, "w") as f:
            if pkg.is_installed:
                changelog += "\n{:=^79}\n".format(" local changelog ")
            f.write(changelog)
        if pkg.is_installed:
            cmd = local_changelog(package, tmp)
            if not cmd:
                return
            perform.execute(cmd)
        with open(tmp) as f:
            for line in f:
                sys.stdout.write(line)


def do_newupgrades(install=False):
    "Display packages that are newly upgraded."

    #
    # Load the dictionaries from file then list each one and it's version
    #
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
            do_install(new_upgrades)


def do_size(packages, size=0):
    "Print sizes for pkg in list PACKAGES with size greater than SIZE."

    # Work with the list of installed packages
    # (I think status has more than installed?)
    status = apt_pkg.TagFile(open("/var/lib/dpkg/status", "r"))
    size_list = dict()
    status_list = dict()

    # Check for information in the Status list
    for section in status:
        if not packages or section.get("Package") in packages:
            package_name   = section.get("Package")
            package_size   = section.get("Installed-Size")
            package_status = re.split(" ", section.get("Status"))[2]
            if package_size and int(package_size) > size:
                if package_name not in size_list:
                    size_list[package_name] = package_size
                    status_list[package_name] = package_status

    pkgs = list(size_list)
    pkgs.sort(key=lambda x: int(size_list[x]))  # sort by size

    if len(pkgs) == 0:
        print("No packages found from those known to be available or installed")
    else:
        print("{:<33} {:^10} {:>12}".format("Package", "Size (KB)", "Status"))
        print("{}-{}-{}".format("="*33, "="*10, "="*12))
        for pkg in pkgs:
            print("{:<33} {:^10} {:>12}".format(pkg,
                    format(int(size_list[pkg]), ',d'), status_list[pkg]))


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


def do_toupgrade():
    "List packages with Available version more recent than Installed."

    # A simple way of doing this is to just list packages in the installed
    # list and the available list which have different versions.
    # However this does not capture the situation where the available
    # package version predates the installed package version (e.g,
    # you've installed a more recent version than in the distribution).
    # So now also add in a call to "dpkg --compare-versions" which slows
    # things down quite a bit!
    print("%-24s %-24s %s" % ("Package", "Available", "Installed"))
    print("="*24 + "-" + "="*24 + "-" + "="*24)

    # List each upgraded pacakge and it's version.
    to_upgrade = changes.get_to_upgrade()
    to_upgrade.sort()
    for i in range(0, len(to_upgrade)):
        print("%-24s %-24s %-24s" % (to_upgrade[i], \
                            changes.get_available_version(to_upgrade[i]), \
                            changes.get_installed_version(to_upgrade[i])))


def do_unhold(packages):
    "Remove packages from hold (they will again be upgraded)."

    for package in packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then.
        command = "echo \"" + package + " install\" | dpkg --set-selections"
        perform.execute(command, root=1)
    print("The following packages are still on hold:")
    perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")


def do_update():
    if not perform.execute("apt-get update", root=1):
        changes.update_available()
        print("There are " + changes.count_upgrades() + " new upgrades")


def do_findpkg(pkg):
    "Look for a particular pkg at apt-get.org."

    ping_host("www.apt-get.org")

    # Print out a suitable heading
    print("Lines suitable for /etc/apt/sources.list\n")
    sys.stdout.flush()

    # Obtain the information from the Apt-Get server
    results = tempfile.mkstemp()[1]
    command = "wget --timeout=60 --output-document=" + results +\
              " http://www.apt-get.org/" +\
              "search.php\?query=" + pkg +\
              "\&submit=\&arch%5B%5D=i386\&arch%5B%5D=all " +\
              "2> /dev/null"
    perform.execute(command)

    # A single page of output
    command = "cat " + results + " | " +\
              "egrep '(^deb|sites and .*packages)' | " +\
              "perl -p -e 's|<[^>]*>||g;s|<[^>]*$||g;s|^[^<]*>||g;'" +\
              "| awk '/^deb/{" +\
              'print "\t", $0;next}/ sites and /' +\
              '{printf "\\n" ;' +\
              "print}'"
    perform.execute(command)

    if os.path.exists(results):
        os.remove(results)


def do_recdownload(packages):
    #FIXME: This has problems with virtual packages, FIX THEM!!!

    """Download packages and all dependencies recursively.
    Author: Juanjo Alvarez <juanjux@yahoo.es>
    """

    def get_deps(package):
        tagfile = apt_pkg.TagFile(open("/var/lib/dpkg/available", "r"))
        deplist = []
        for section in tagfile:
            if section.get("Package") == package:
                deplist = apt_pkg.parse_depends(section.get("Depends", ""))
                break
        realdeplist = []
        if deplist != []:
            for i in deplist:
                realdeplist.append((i[0][0], i[0][1]))
        return realdeplist

    def get_deps_recursively(package, packageslist):
        if not package in packageslist:
            packageslist.append(package)
        for packageName, versionInfo in get_deps(package):
            if packageName not in packageslist:
                packageslist.append(packageName)
                get_deps_recursively(packageName, packageslist)
        return packageslist

    packageNames = []
    dontDownloadList = []
    for package in packages[:]:
        # Ignore packages with a "-" at the end so the user can workaround some
        # dependencies problems (usually in unstable)
        if package[len(package) - 1:] == "-":
            dontDownloadList.append(package[:-1])
            packages.remove(package)
            continue

    print("Calculating all dependencies...")
    for i in packages:
        tmp = get_deps_recursively(i, [])
        for i in tmp:
            # We don't want dupplicated package names
            # and we don't want package in the dontDownloadList
            if i in dontDownloadList:
                continue
            if i not in packageNames:
                packageNames.append(i)
    print("Packages to download to /var/cache/apt/archives:")
    for i in packageNames:
        # We do this because apt-get install dont list the packages to
        # reinstall if they don't need to be upgraded
        print(i, end=' ')
    print("\n")

    command = "apt-get --download-only --reinstall -u install " \
    + util.concat(packageNames)
    perform.execute(command, root=1)


def versions(packages):
    if len(packages) == 0:
        perform.execute("apt-show-versions")
    else:
        for package in packages:
            perform.execute("apt-show-versions " + package)


def rbuilddep(package):
    cmd = "grep-available -sPackage -FBuild-Depends,Build-Depends-Indep " + \
          package + " /var/lib/apt/lists/*Sources"
    perform.execute(cmd)
