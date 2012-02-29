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
import subprocess

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

available_file = changes.available_file
previous_file  = changes.previous_file



def do_new():
    "Report on packages that are newly available."

    print("%-24s %s" % ("Package", "Available"))
    print("="*24 + "-" + "="*16)
    #
    # List each package and it's version
    #
    new_packages = changes.get_new_available()
    new_packages.sort()
    for i in range(0, len(new_packages)):
        print("%-24s %s" % (new_packages[i],
            changes.get_available_version(new_packages[i])))









def addcdrom(args):
    """
    Add a Debian CD/DVD to APT's list of available sources
    $ wajig addcdrom
    
    note: this runs 'apt-cdrom add'
    """
    util.requires_no_args("addcdrom", args)
    perform.execute("apt-cdrom add", root=True)


def addrepo(args):
    """
    Add a Launchpad PPA (Personal Package Archive) repository
    Here's an example that shows how to add the daily builds of
    Google's Chromium browser:
    $ wajig addrepo ppa:chromium-daily      (add-apt-repository)
    """
    util.requires_one_arg("addrepo", args,
                         "a PPA (Personal Package Archive) repository to add")
    util.requires_package("add-apt-repository", "/usr/bin/add-apt-repository")
    perform.execute("add-apt-repository " + args[1], root=True)


def autoalts(args):
    """
    Mark the Alternative to be auto-set (using set priorities).
    $ wajig autoalts <alternative name>

    note: this runs 'update-alternatives --auto'
    """
    util.requires_one_arg("autoalts", args, "name alternative to set as auto")
    perform.execute("update-alternatives --auto " + args[1], root=True)


def autodownload(args, verbose):
    """
    Do an update followed by a download of all updated packages
    $ wajig autodownload
    
    note: this runs 'apt-get -d -u -y dist-upgrade'
    """
    util.requires_no_args("autodownload", args)
    if verbose:
        util.do_update()
        filter_str = ""
    else:
        util.do_update()
        filter_str = '| egrep -v "(http|ftp)"'
    perform.execute("apt-get --download-only --show-upgraded " + \
                    "--assume-yes dist-upgrade " + filter_str,
                    root=True)
    util.do_describe_new(verbose)
    util.do_newupgrades()


def autoclean(args):
    """
    Remove no-longer-downloadable .deb files from the download cache
    $ wajig autoclean

    note: this runs 'apt-get autoclean'
    """
    util.requires_no_args("autodownload", args)
    perform.execute("apt-get autoclean", root=True)


def autoremove(args):
    """
    Remove unused dependency packages
    $ wajig autoremove
    """
    util.requires_no_args("autoremove", args)
    perform.execute("apt-get autoremove", root=True)


def reportbug(args):
    """
    Report a bug in a package using Debian BTS (Bug Tracking System)
    $ wajig bug <package name>

    note: this runs 'reportbug'
    """
    util.requires_one_arg("reportbug", args, "a single named package")
    util.requires_package("reportbug", "/usr/bin/reportbug")
    perform.execute("reportbug " + args[1])


def build(args, yes, noauth):
    """
    Retrieve source packages, unpack them, and build binary (.deb) packages
    from them. This also installs the needed build-dependencies if needed.
    $ wajig buld <package names>

    options:
      -n --noauth       install and build even if package(s) is untrusted
      -y --yes          install/download without yes/no prompts; use with care!

    note: this runs 'apt-get build-dep && apt-get source --build'
    """
    util.requires_args("build", args, "a list of package names")
    util.requires_package("sudo", "/usr/bin/sudo")
    # First make sure dependencies are met
    command = "apt-get {} {} build-dep " + " ".join(args[1:])
    command = command.format(yes, noauth)
    result = perform.execute(command, root=True)
    if not result:
        command = "apt-get {} source --build " + " ".join(args[1:])
        command = command.format(noauth)
        perform.execute(command, root=True)


def builddeps(args, yes, noauth):
    """
    Install build-dependencies for given packages.
    $ wajig builddep <package names>

    long form command: reverse-build-depends

    options:
      -n --noauth       install even if package is untrusted
      -y --yes          install without yes/no prompts; use with care!

    note: this runs 'apt-get build-dep'
    """
    util.requires_args("builddepend", args, "a list of package names")
    command = "apt-get {} {} build-dep " + " ".join(args[1:])
    command = command.format(yes, noauth)
    perform.execute(command, root=True)


def rbuilddeps(args):
    """
    Display the packages which build-depend on the given package
    $ wajig rbuilddeps PKG
    """
    util.requires_one_arg("rbuilddeps", args, "one package name")
    util.requires_package("grep-dctrl", "/usr/bin/grep-dctrl")
    command = "grep-available -sPackage -FBuild-Depends,Build-Depends-Indep "
    command = command + args[1] + " /var/lib/apt/lists/*Sources"
    perform.execute(command)


def changelog(args, verbose):
    """
    Display Debian changelog of a package
    $ wajig changelog <package name>

    network on:
         changelog - if there's newer entries, display them
      -v changelog - if there's newer entries, display them, and proceed to
                     display complete local changelog

    network off:
         changelog - if there's newer entries, mention failure to retrieve
      -v changelog - if there's newer entries, mention failure to retrieve, and
                     proceed to display complete local changelog
    """
    util.requires_one_arg("changelog", args, "one package name")
    package_name = args[1]
    util.package_exists(package_name)

    changelog = "{:=^79}\n".format(" {} ".format(package_name))  # header

    package = apt.Cache()[package_name]
    try:
        changelog += package.get_changelog()
    except AttributeError as e:
        # This is caught so as to avoid an ugly python-apt trace; it's a bug
        # that surfaces when:
        # 1. The package is not available in the default Debian suite
        # 2. The suite the package belongs to is set to a pin of < 0
        print("If this package is not on your default Debian suite, " \
              "ensure that it's APT pinning isn't less than 0.")
        return
    help_message = "\nTo display the local changelog, run:\n" \
                   "wajig --verbose changelog " + package_name
    if "Failed to download the list of changes" in changelog:
        if not verbose:
            changelog += help_message
        else:
            changelog += "\n"
    elif changelog.endswith("The list of changes is not available"):
        changelog += ".\nYou are likely running the latest version.\n"
        if not verbose:
            changelog += help_message
    if not verbose:
        print(changelog)
    else:
        tmp = tempfile.mkstemp()[1]
        with open(tmp, "w") as f:
            if package.is_installed:
                changelog += "{:=^79}\n".format(" local changelog ")
            f.write(changelog)
        if package.is_installed:
            command = util.local_changelog(package_name, tmp)
            if not command:
                return
            perform.execute(command)
        with open(tmp) as f:
            for line in f:
                sys.stdout.write(line)


def clean(args):
    """
    Remove all deb files from the download cache
    $ wajig clean

    note: this runs 'apt-get clean'
    """
    util.requires_no_args("clean", args)
    perform.execute("apt-get clean", root=True)


def contents(args):
    """
    List the contents of a package file (.deb)
    $ wajig contents <deb file>
    
    note: this runs 'dpkg --contents'
    """
    util.requires_one_arg("contents", args, "a single filename")
    perform.execute("dpkg --contents " + args[1])


def dailyupgrade(args):
    """
    Perform an update then a dist-upgrade
    $ wajg daily-upgrade
    
    note: this runs 'apt-get --show-upgraded dist-upgrade'
    """
    util.requires_no_args("dailyupgrade", args)
    util.do_update()
    perform.execute("apt-get --show-upgraded dist-upgrade", root=True)


def dependents(args):
    """
    Display packages which have some form of dependency on the given package

    Types of dependencies:
    * Depends
    * Recommends
    * Suggests
    * Replaces
    * Enhances

    $ wajig dependents <package name>
    """
    util.requires_one_arg("dependents", args, "one package name")
    package = args[1]

    DEPENDENCY_TYPES = [
        "Depends",
        "Recommends",
        "Suggests",
        "Replaces",
        "Enhances",
    ]

    cache = apt.cache.Cache()
    try:
        package = cache[package]
    except KeyError as error:
        print(error.args[0])
        sys.exit(1)

    dependents = { name : [] for name in DEPENDENCY_TYPES }

    for key in cache.keys():
        other_package = cache[key]
        for dependency_type, specific_dependents in dependents.items():
            if package.shortname in util.extract_dependencies(other_package, dependency_type):
                specific_dependents.append(other_package.shortname)

    for dependency_type, specific_dependents in dependents.items():
        if specific_dependents:
            output = dependency_type.upper(), " ".join(specific_dependents)
            print("{}: {}".format(*output))


def describe(args, verbose):
    """
    Display the short description of a package(s)
    $ wajig describe <package name>

    options:
      -v  --verbose     display long description as well
    """
    util.requires_args("describe", args, "a list of packages")
    util.do_describe(args[1:], verbose)


def describenew(args, verbose):
    """
    One line descriptions of new packages
    $ wajig describe-new
    """
    util.requires_no_args("describe", args)
    util.do_describe_new(verbose)


def distupgrade(args, yes, noauth):
    """
    Complete system upgrade; this may remove some packages if they are on the way
    $ wajig dist-upgrade

    note: this runs 'apt-get --show-upgraded distupgrade'
    """
    packages = util.upgradable(distupgrade=True)
    if not packages and len(args) < 2:
        print('No upgrades. Did you run "wajig update" beforehand?')
    elif util.requires_opt_arg("distupgrade", args,
                              "the distribution to upgrade to"):
        if backup \
        and util.requires_package("dpkg-repack", "/usr/bin/dpkg-repack") \
        and util.requires_package("fakeroot", "/usr/bin/fakeroot"):
            changes.backup_before_upgrade(packages, distupgrade=True)
        cmd = "apt-get --show-upgraded {0} {1} ".format(yes, noauth)
        if len(args) == 2:
            cmd += "-t " + args[1] + " "
        cmd += "dist-upgrade"
        perform.execute(cmd, root=True)


def download(args):
    """
    Download one or more packages without installing them
    $ wajig download <package name(s)>

    note: this runs 'apt-get --reinstall --download-only install'
    """
    util.requires_args("download", args, "a list of packages")
    packages = args[1:]

    # Print message here since no messages are printed for the command.
    print("Packages being downloaded to /var/cache/apt/archives/")

    # Do the download, non-interactively (--quiet),
    # and force download for already installed packages (--reinstall)
    command = "apt-get --reinstall --download-only install "
    command = command + " ".join(packages)
    a = perform.execute(command, root=True)


def editsources(args):
    """
    Edit list of archives which locates Debian package sources
    $ wajig editsources

    note: this runs 'editor /etc/apt/sources.list'
    """
    util.requires_no_args("editsources", args)
    perform.execute("editor /etc/apt/sources.list", root=True)


def extract(args):
    """
    Extract the files from a package file to a directory
    $ wajig extract <deb file> <destination directory>
    """
    util.requires_two_args("extract", args,
                           "a filename and directory to extract into")
    perform.execute("dpkg --extract {0} {1}".format(args[1], args[2]))


def fixconfigure(args):
    """
    Fix an interrupted install
    $ wajig fix-configure

    note: this runs 'dpkg --configure --pending'
    """
    util.requires_no_args("fixconfigure", args)
    perform.execute("dpkg --configure --pending", root=True)


def fixinstall(args, noauth):
    """
    Fix an install interrupted by broken dependencies
    $ wajig fixinstall

    note: this runs 'apt-get --fix-broken install
    """
    util.requires_no_args("fixinstall", args)
    perform.execute("apt-get --fix-broken {} install".format(noauth),
                     root=True)


def fixmissing(args, noauth):
    """
    Fix and install even though there are missing dependencies.
    $ wajig fix-missing

    note: this runs 'apt-get --ignore-missing'
    """
    util.requires_no_args("fixmissing", args)
    command = "apt-get --ignore-missing {} upgrade".format(noauth)
    perform.execute(command, root=True)


def force(args):
    """
    Install packages and ignore file overwrites and depends.
    $ wajig force <package name(s)>
    
    note: This is useful when there is a conflict of the same file from
          multiple packages or when a dependency is not installed for
          whatever reason.
    """
    util.requires_args("force", args, "a package name")
    packages = args[1:]

    command = "dpkg --install --force overwrite --force depends "
    archives = "/var/cache/apt/archives/"

    # For a .deb file we simply force install it.
    if re.match(".*\.deb$", packages[0]):
        for package in packages:
            if os.path.exists(package):
                command += "'" + package + "' "
            elif os.path.exists(archives + package):
                command += "'" + archives + package + "' "
            else:
                print("""File `%s' not found.
              Searched current directory and %s.
              Please confirm the location and try again.""" % (package, archives))
                return()
    else:
        # Package names rather than a specific deb package archive
        # is expected.
        for package in packages:
            # Identify the latest version of the package available in
            # the download archive, if there is any there.
            lscmd = "/bin/ls " + archives
            lscmd += " | egrep '^" + package + "_' | sort -k 1b,1 | tail -n -1"
            matches = perform.execute(lscmd, pipe=True)
            debpkg = matches.readline().strip()

            if not debpkg:
                dlcmd = "apt-get --quiet=2 --reinstall --download-only "
                dlcmd += "install '" + package + "'"
                perform.execute(dlcmd, root=1)
                matches = perform.execute(lscmd, pipe=True)
                debpkg = matches.readline().strip()

            # Force install the package from the download archive.
            command += "'" + archives + debpkg + "' "

    perform.execute(command, root=1)


def help(args):
    """
    Print usage info on commands
    $ wajig help COMMAND(s)
    """
    util.requires_args("help", args, "wajig commands(s)")
    for command in args[1:]:
        command = command.replace("-", "")
        command = command.replace("_", "")
        command = command.lower()
        if command == "autoalternatives":
            command = "autoalts"
        elif command in "builddepend builddepends builddeps".split():
            command = "builddeps"
        elif command in "doc docs documentation".split():
            command = "tutorial"
        elif command in ["rbuilddep", "reversebuilddeps",
                         "reversebuilddependencies"]:
            command = "rbuilddeps"
        elif command in ["findpkg", "findpackage"]:
            command = "unofficial"
        elif command == "available":
            command = "policy"
        elif command == "statussearch":
            command = "statusmatch"
        elif command == "size":
            command = "sizes"
        elif command == "rpmtodeb":
            command = "rpm2deb"
        elif command in "bug bugreport".split():
            command = "reportbug"
        elif command == "purgedepend":
            command = "purge"
        elif command == "commands":
            command = "listcommands"
        elif command == "recursive":
            command = "recdownload"
        elif command == "newdescribe":
            command = "describenew"
        elif command == "package":
            command = "repackage"
        elif command == "detailnew":
            command = "newdetail"
        elif command == "list":
            command = "listpackages"
        elif command == "listlog":
            command = "syslog"
        elif command in "orphaned listorphaned listorphans".split():
            command = "orphans"
        elif command == "listalts":
            command = "listalternatives"
        elif command == "newupgrade":
            command = "newupgrades"
        elif command in ["detail", "details"]:
            command = "show"
        elif command in "installs suggested".split():
            command = "installsuggested"
        elif command in ["isntall", "autoinstall"]:
            command = "install"
        elif command in "findfile locate filesearch whichpkg".split():
            command = "whichpackage"
        util.help(command)


def hold(args):
    """
    Place packages on hold (so they will not be upgraded)
    $ wajig hold <package names>
    """
    util.requires_args("hold", args, "a list of packages to place on hold")
    for package in args[1:]:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then!
        command = "echo \"" + package + " hold\" | dpkg --set-selections"
        perform.execute(command, root=True)
    print("The following packages are on hold:")
    perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")


def info(args):
    """
    List the information contained in a package file.
    $ wajig info
    
    note: this runs 'dpkg --info'
    """
    util.requires_one_arg("info", args, "one filename")
    perform.execute("dpkg --info " + args[1])


def init(args):
    """
    Initialise or reset wajig archive files.
    $ wajig init
    """
    util.requires_no_args("init", args)
    changes.reset_files()


def install(command, args, yes, noauth, dist):
    """
    Install one or more packages or .deb files, or via a url

    $ wajig install <package name(s)>
    $ wajig install <deb filename(s)>
    $ wajig install http://example.com/<deb filename>

    options:
      -n --noauth       install even if package is untrusted
      -y --yes          install without yes/no prompts; use with care!
      -r|--recommends   install Recommends (this is Debian default)
      -R|--norecommends do NOT install Recommends
         --dist         select which Debian suite to regard as default

    example:
    $ wajig --noauth --yes --norecommends --dist experimental <package names>

    The above command installs the <package name> version from Experimental
    suite, if available. It also disregard the situation where the package
    can't be authenticated (e.g. the package cache is not updated or the
    keyring isn't installed).  At the same don't prompt for confirmation, and
    also, don't install packages Recommended by <package names>.

    Note that, unlike using 'dpkg -i', installing a deb file will also install
    its dependencies. The output is ugly though, so be not alarmed.
    """
    util.requires_args(command, args, "packages, .deb files, or a url")
    # kept so as not to break anyone's setup; consider it deprecated;
    # it's not even advertised no more (removed from docs)
    if command == "autoinstall":
        yes = "--yes"
    packages = args[1:]

    # Currently we use the first argument to determine the type of all
    # of the rest. Perhaps we should look at each one in turn?
    #
    # Handle URLs first. We don't do anything smart.  Simply download
    # the .deb file and install it.  If it fails then don't attempt to
    # recover.  The user can do a wget themselves and install the
    # resulting .deb if they need to.
    #
    # Currently only a single URL is allowed. Should this be generalised?

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
        command = "apt-get {} {} {} {} install " + " ".join(packages)
        command = command.format(yes, noauth, rec, dist)
        perform.execute(command, root=True)


def installsuggested(args, yes, noauth, dist):
    """
    Install a package and its Suggests dependencies.
    $ wajig installs <package name>
    """
    util.requires_one_arg("installsuggested", args, "a single package name")
    package_name = args[1]
    cache = apt.cache.Cache()
    try:
        package = cache[package_name]
    except KeyError as error:
        print(error.args[0])
        sys.exit(1)
    dependencies = " ".join(util.extract_dependencies(package, "Suggests"))
    template = "apt-get {0} {1} {2} --show-upgraded install {3} {4}"
    command = template.format(util.recommends(), yes, noauth, dependencies,
                          package_name)
    perform.execute(command, root=True)


def installwithdist(args, yes, noauth, dist):
    """
    Install a package from while specifying a suite to install from
    $ wajig install/experimental
    """
    util.requires_args("installwithdist", args,
                       "a list of packages, .deb files, or url")
    dist = args[0].split("/")[1]
    command = "apt-get --target-release {} install " + " ".join(args[1:])
    command = command.format(dist)
    perform.execute(command, root=True)


def integrity(args):
    """
    Check the integrity of installed packages (through checksums).
    $ wajig integrity

    notes: this runs 'debsums --all --silent'
    """
    util.requires_no_args("integrity", args)
    perform.execute("debsums --all --silent")


def large(args):
    """
    List size of all large (>10MB) installed packages.
    $ wajig large
    """
    util.requires_no_args("large", args)
    packages = args[1:]
    size = 10000

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

    packages = list(size_list)
    packages.sort(key=lambda x: int(size_list[x]))  # sort by size

    if packages:
        print("{:<33} {:^10} {:>12}".format("Package", "Size (KB)", "Status"))
        print("{}-{}-{}".format("="*33, "="*10, "="*12))
        for package in packages:
            print("{:<33} {:^10} {:>12}".format(package,
                    format(int(size_list[package]), ',d'), status_list[package]))
    else:
        print("No packages found from those known to be available or installed")


def lastupdate(args):
    """
    Identify when an update was last performed
    $ wajig last-update
    """
    util.requires_no_args("lastupdate", args)
    command = ("/bin/ls -l --full-time " + changes.available_file + " 2> "
               "/dev/null | awk '{printf \"Last update was %s %s %s\\n\""
               ", $6, $7, $8}' | sed 's|\.000000000||'")
    perform.execute(command)


def listcache(args):
    """
    List the contents of the download cache
    $ wajig list-cache
    """
    util.requires_opt_arg("listcache", args, "string to filter on")
    command = "printf 'Found %d files %s in the cache.\n\n'\
           $(ls /var/cache/apt/archives/ | wc -l) \
           $(ls -sh /var/cache/apt/archives/ | head -1 | awk '{print $2}')"
    perform.execute(command)
    command = "ls /var/cache/apt/archives/"
    if len(args) == 2:
        command = command + " | grep '" + args[1] + "'"
    command += "; echo"
    perform.execute(command)


def listcommands(args):
    """
    List all the JIG commands and one line descriptions for each.
    $ wajig list-commands
    """
    util.requires_no_args("listcommands", args)
    with open("/usr/share/wajig/help/COMMANDS") as f:
        print()
        for line in f:
            print(line, end=' ')
        print()


def listalternatives(args):
    """
    List the objects that can have alternatives configured
    $ wajig list-alternatives
    """
    util.requires_no_args("listalternatives", args)
    command = ("ls /etc/alternatives/ | "
               "egrep -v '(\.1|\.1\.gz|\.8|\.8\.gz|README)$'")
    perform.execute(command)


def listdaemons(args):
    """
    List the daemons that wajig can start/stop/restart
    $ wajig list-daemons
    """
    util.requires_no_args("listdaemons", args)
    command = ("printf 'Found %d daemons in /etc/init.d.\n\n' "
               "$(ls /etc/init.d/ | "
               "egrep -v '(~$|README|-(old|dist)|\.[0-9]*$)' | wc -l)")
    perform.execute(command)
    command = ("ls /etc/init.d/ | "
               "egrep -v '(~$|README|-(old|dist)|\.[0-9]*$)' |"
               "pr --columns=3 --omit-header")
    perform.execute(command)


def listfiles(args):
    """
    List the files that are supplied by the named package
    $ wajig list-files
    """
    util.requires_one_arg("listfiles", args,
                          "the name of a single Debian package or deb file")
    package = args[1]
    if package.endswith("deb"):
        perform.execute("dpkg --contents " + args[1])
    else:
        perform.execute("dpkg --listfiles " + args[1])


def listhold(args):
    """
    List packages that are on hold (i.e. those that won't be upgraded)
    $ wajig list-hold
    """
    util.requires_no_args("listhold", args)
    perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")


def listinstalled(args):
    """
    List installed packages
    $ wajig list-installed
    """
    util.requires_no_args("listinstalled", args)
    perform.execute("dpkg --get-selections | cut -f1")


def listnames(args):
    """
    List all known packages; optionally filter the list with a pattern
    $ wajig list-names [<pattern>]
    """
    util.requires_opt_arg("listnames", args, "at most one argument")
    util.do_listnames(args[1:])


def listpackages(args):
    """
    List the status, version, and description of installed packages
    $ wajig list
    """
    util.requires_opt_arg("listpackages", args, "string to filter on")
    cmd = ""
    cmd += "dpkg --list '*' | grep -v 'no description avail'"
    if len(args) > 1:
        cmd += " | egrep '" + args[1] + "' | sort -k 1b,1"
    perform.execute(cmd)


def listscripts(args):
    """
    List the control scripts of the package of deb file
    $ wajig list-scripts <.deb file>
    """
    util.requires_one_arg("listscripts", args, "a package name or deb file")
    package = args[1]
    scripts = ["preinst", "postinst", "prerm", "postrm"]
    if re.match(".*\.deb$", package):
        command = "ar p " + package + " control.tar.gz | tar ztvf -"
        pkgScripts = perform.execute(command, pipe=True).readlines()
        for script in scripts:
            if "./" + script in "".join(pkgScripts):
                nlen = int((72 - len(script)) / 2)
                print(">"*nlen, script, "<"*nlen)
                command = "ar p " + package + " control.tar.gz |" +\
                          "tar zxvf - -O ./" + script +\
                          " 2>/dev/null"
                perform.execute(command)
    else:
        root = "/var/lib/dpkg/info/"
        for script in scripts:
            fname = root + package + "." + script
            if os.path.exists(fname):
                nlen = (72 - len(script))/2
                print(">"*nlen, script, "<"*nlen)
                perform.execute("cat " + fname)




def listsection(args):
    """
    List packages that belong to a specific section.
    $ wajig list-section <section name>

    note: Use the LIST-SECTIONS command for a list of Debian Sections
    """
    util.requires_one_arg("listsection", args, "the name of a Debian Section")
    section = args[1]
    cache = apt.cache.Cache()
    for package in cache.keys():
        package = cache[package]
        if(package.section == section):
            print(package.name)


def liststatus(args):
    """
    Same as list but only prints first two columns, not truncated.
    $ wajig list-status
    """
    util.requires_opt_arg("liststatus", args, "package name")
    cmd = "COLUMNS=400 "
    cmd += "dpkg --list '*' | grep -v 'no description avail'"
    cmd += " | awk '{print $1,$2}'"
    if len(args) > 1:
        cmd += " | egrep '" + args[1] + "' | sort -k 1b,1"
    perform.execute(cmd)


def localdistupgrade(args):
    """
    Dist-upgrade using only packages that are already downloaded
    $ wajig local-dist-upgrade
    """
    util.requires_no_args("localdistupgrade", args)
    command = ("apt-get --no-download --ignore-missing "
               "--show-upgraded dist-upgrade")
    perform.execute(command, root=True)


def localupgrade(args):
    """
    Upgrade using only packages that are already downloaded
    $ wajig local-upgrade
    """
    util.requires_no_args("localupgrade", args)
    command = "apt-get --no-download --ignore-missing --show-upgraded upgrade"
    perform.execute(command, root=True)


def listsections(args):
    """
    List all available sections
    $ wajig list-sections
    """
    util.requires_no_args("listsections", args)
    cache = apt.cache.Cache()
    sections = list()
    for package in cache.keys():
        package = cache[package]
        sections.append(package.section)
    sections = set(sections)
    for section in sections:
        print(section)


def madison(args):
    """
    Runs the madison command of apt-cache
    $ wajig madison <package name(s)>

    note: this runs 'apt-cache madison'
    """
    util.requires_args("madison", args, "package name(s)")
    perform.execute("apt-cache madison " + " ".join(set(args[1:])))


def nonfree(args):
    """
    List installed packages that do not meet the DFSG.
    $ wajig non-free
    """
    util.requires_no_args("nonfree", args)
    util.requires_package("vrms", "/usr/bin/vrms")
    perform.execute("vrms")


def move(args):
    """
    Move packages in the download cache to a local Debian mirror
    $ wajig move
    """
    util.requires_no_args("move", args)
    perform.execute("apt-move update", root=True)


def new(args):
    """
    List packages that became available since last update
    $ wajig new
    """
    util.requires_opt_arg("new", args, "whether to INSTALL the new pkgs")
    if len(args) == 1:
        util.do_describe_new()
    elif args[1].lower() == "install":
        util.do_describe_new(install=True)
    else:
        print("NEW only accepts optional argument INSTALL")


def newdetail(args):
    """
    Provide a detailed description of new packages
    $ wajig detail-new
    """
    util.requires_no_args("newdetail", args)
    new_packages = changes.get_new_available()
    if new_packages:
        package_names = " ".join(new_packages)
        command = "apt-cache" if util.fast else "aptitude"
        perform.execute("{} show {}".format(command, package_names))
    else:
        print("No new packages available")


def news(command, args):
    """
    Display the NEWS file of a given package
    $ wajig news <package name>
    """
    util.requires_one_arg(command, args, "a single package")
    util.display_sys_docs(args, "NEWS.Debian NEWS")


def newupgrades(args, yes, noauth):
    """
    List packages newly available for upgrading
    $ wajig new-upgrades
    """
    util.requires_opt_arg("newupgrades", args,
                          "whether to INSTALL upgraded pkgs")
    if len(args) == 1:
        util.do_newupgrades()
    elif args[1].lower() == "install":
        util.do_newupgrades(install=True)
    else:
        print("NEWUPGRADES only accepts " + \
              "optional argument INSTALL")
        util.finishup(1)


def orphans(args):
    """
    List libraries not required by any installed package
    $ wajig orphans
    """
    util.requires_no_args("orphans", args)
    util.requires_package("deborphan", "/usr/bin/deborphan")
    perform.execute("deborphan")


def policy(args):
    """
    From preferences file show priorities/policy (available).
    $ wajig policy <package name>

    note: this runs 'apt-cache policy'
    """
    util.requires_args("policy", args, "a package or packages")
    perform.execute("apt-cache policy " + " ".join(args[1:]))


def purge(args, yes, noauth):
    """
    Remove one or more packages and their configuration files.
    $ wajig purge <package name(s)>

    options:
      -n --noauth   skip the authentication verification prompt before the upgrade
      -y --yes      purge without (yes/no) prompts; use with care!

    note: this runs 'apt-get --auto-remove purge'
    """
    util.requires_args("purge", args, "a list of packages")
    command = "apt-get {0} {1} --auto-remove purge ".format(yes, noauth)
    command = command + " ".join(args[1:])
    perform.execute(command, root=True)


def purgeorphans(args):
    """
    Purge orphaned libraries (not required by installed packages).
    $ wajig purge-orphans
    """
    # Deborphans does not require root, but dpkg does,
    # so build up the orphans list first, then pass that to dpkg.
    util.requires_no_args("purgeorphans", args)
    util.requires_package("deborphan", "/usr/bin/deborphan")
    packages = ""
    for package in perform.execute("deborphan", pipe=True):
        packages += " " + package.strip()
    if packages:
        perform.execute("apt-get purge" + packages, root=True)


def purgeremoved(args):
    """
    Purge all packages marked as deinstall
    $ wajig purge-removed
    """
    util.requires_no_args("purgeremoved", args)
    packages = ""
    cmd = ("dpkg-query --show --showformat='${Package}\t${Status}\n' | "
           "grep \"deinstall ok config-files\" | cut -f 1 ")
    for package in perform.execute(cmd, pipe=True):
        packages += " " + package.strip()
    if packages:
        perform.execute("apt-get purge" + packages, root=True)


def readme(command, args):
    """
    Display the README file of a given package
    $ wajig readme <package name>
    """
    util.requires_one_arg(command, args, "a single package")
    util.display_sys_docs(args, "README README.Debian USAGE")


def recdownload(args):
    """
    Download a package and all its dependencies
    $ wajig recursive <package name>
    """
    util.requires_args("recdownload", args, "a list of packages")
    packages = args[1:]

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

    package_names = list()
    dontDownloadList = list()
    for package in packages:
        # Ignore packages with a "-" at the end so the user can workaround some
        # dependencies problems (usually in unstable)
        if package[len(package) - 1:] == "-":
            dontDownloadList.append(package[:-1])
            packages.remove(package)

    print("Calculating all dependencies...")
    for i in packages:
        tmp = get_deps_recursively(i, [])
        for i in tmp:
            # We don't want dupplicated package names
            # and we don't want package in the dontDownloadList
            if i not in package_names:
                package_names.append(i)
    print("Packages to download to /var/cache/apt/archives:")
    for i in package_names:
        # We do this because apt-get install dont list the packages to
        # reinstall if they don't need to be upgraded
        print(i, end=' ')
    print("\n")

    command = "apt-get --download-only --reinstall -u install " + \
              " ".join(package_names)
    perform.execute(command, root=True)


def reconfigure(args):
    """
    Reconfigure a few packages
    $ wajig reconfigure <package name(s)>

    note: this runs 'dpkg-reconfigure'
    """
    util.requires_args("reconfigure", args, "one or more packages")
    command = "dpkg-reconfigure " + " ".join(args[1:])
    perform.execute(command, root=True)


def recommended(args):
    """
    Display packages that were installed via Recommends and have no dependents.
    $ wajig list-recommended
    """
    util.requires_no_args("recommended", args)
    command = ("aptitude search '"
              "?and( ?automatic(?reverse-recommends(?installed)), "
              "?not(?automatic(?reverse-depends(?installed))) )'")
    perform.execute(command)


def reload(args):
    """
    Reload system daemons (see LIST-DAEMONS for available daemons)
    $ wajig reload DAEMON

    notes: this runs 'service DAEMON reload'
    """
    util.requires_one_arg(args[0], args, "name of service to " + args[0])
    command = "service {} {}".format(args[1], args[0])
    if perform.execute(command, root=True):
        print("attempt FORCE-RELOAD instead")
        command = "service {} force-reload ".format(args[1])
        perform.execute(command, root=True)


def remove(args, noauth, yes):
    """
    Remove packages (see also PURGE command)
    $ wajig remove <package name(s)>

    options:
      -n --noauth   reinstall even if package is untrusted
      -y --yes      remove without (yes/no) prompts; use with care!

    note: this runs 'apt-get --auto-remove remove'
    """
    util.requires_args("remove", args, "a list of packages")
    command = "apt-get {0} {1}--auto-remove remove " + " ".join(args[1:])
    command = command.format(yes, noauth)
    perform.execute(command, root=True)


def removeorphans(args):
    """
    Remove orphaned libraries
    $ wajig remove-orphans
    """
    util.requires_no_args("removeorphans", args)
    util.requires_package("deborphan", "/usr/bin/deborphan")
    packages = ""
    for package in perform.execute("deborphan", pipe=True):
        packages += " " + package.strip()
    if packages:
        perform.execute("apt-get remove" + packages, root=True)


def repackage(args):
    """
    Generate a .deb file for an installed package.
    $ wajig repackage <package name>

    note: this runs 'fakeroot -u dpkg-repack'
    """
    util.requires_one_arg("repackage", args, "name of an installed package")
    util.requires_package("dpkg-repack", "/usr/bin/dpkg-repack")
    util.requires_package("fakeroot", "/usr/bin/fakeroot")
    command = "fakeroot --unknown-is-real dpkg-repack " + args[1]
    perform.execute(command, root=False)


def restart(args):
    """
    Restart system daemons (see LIST-DAEMONS for available daemons)
    $ wajig restart DAEMON

    notes: this runs 'service DAEMON restart'
    """
    util.requires_one_arg(args[0], args, "name of service to " + args[0])
    command = "service {} {}".format(args[1], args[0])
    perform.execute(command, root=True)


def rpm2deb(args):
    """
    Convert an .rpm file to a Debian .deb file
    $ wajig rpm2deb <rpm file>

    note: this runs 'alien'
    """
    util.requires_one_arg("rpm2deb", args, "a .rpm file")
    command = "alien " + args[1]
    perform.execute(command, root=True)


def rpminstall(args):
    """
    Install an .rpm package file
    $ wajig rpminstall <rpm file>

    note: this runs 'alien --install'
    """
    util.requires_one_arg("rpminstall", args,
                          "a single .rpm file")
    command = "alien --install " + args[1]
    perform.execute(command, root=True)


def search(args, verbose):
    """
    Search for package names containing the given pattern
    $ wajig search <pattern>

    options:
      -v --verbose  also search package descriptions
    """
    util.requires_args("search", args, "a list of words to search for")
    if verbose:
        command = "apt-cache search " + " ".join(args[1:])
    else:
        command = "apt-cache search --names-only " + " ".join(args[1:])
    perform.execute(command)


def searchapt(args):
    """
    Find nearby Debian archives that are suitable for /etc/apt/sources.list
    $ wajig search-apt

    note: this runs 'netselect-apt'
    """
    util.requires_one_arg("searchapt", args, "one of stable|testing|unstable")
    util.requires_package("netselect-apt", "/usr/bin/netselect-apt")
    command = "netselect-apt " + args[1]
    perform.execute(command, root=True)


def showdistupgrade(args):
    """
    Trace the steps that a dist-upgrade would perform
    $ wajig showdistupgrade

    note: this runs 'apt-get --show-upgraded --simulate dist-upgrade'
    """
    util.requires_no_args("showdistupgrade", args)
    command = "apt-get --show-upgraded --simulate dist-upgrade"
    perform.execute(command, root=True)


def showinstall(args):
    """
    Trace the steps that an install would perform.
    $ wajig showinstall <package name(s)>

    note: this runs 'apt-get --show-upgraded --simulate install'
    """
    util.requires_args("showinstall", args, "a list of packages")
    command = "apt-get --show-upgraded --simulate install " + " ".join(args[1:])
    perform.execute(command, root=True)


def showremove(args):
    """
    Trace the steps that a remove would perform
    $ wajig showremove <package name(s)>

    note: this runs 'apt-get --show-upgraded --simulate remove'
    """
    util.requires_args(command, args, "a list of packages")
    command = "apt-get --show-upgraded --simulate remove " + " ".join(args[1:])
    perform.execute(command, root=True)


def showupgrade(args):
    """
    Trace the steps that an upgrade would perform
    $ wajig showupgrade

    note: this runs 'apt-get --show-upgraded --simulate upgrade'
    """
    util.requires_no_args(command, args)
    command = "apt-get --show-upgraded --simulate upgrade"
    perform.execute(command, root=True)


def start(args):
    """
    Start system daemons (see LIST-DAEMONS for available daemons)
    $ wajig start DAEMON

    notes: this runs 'service DAEMON start'
    """
    util.requires_one_arg(args[0], args, "name of service to " + args[0])
    command = "service {} {}".format(args[1], args[0])
    perform.execute(command, root=True)


def stop(args):
    """
    Stop system daemons (see LIST-DAEMONS for available daemons)
    $ wajig stop DAEMON

    notes: this runs 'service DAEMON stop'
    """
    util.requires_one_arg(args[0], args, "name of service to " + args[0])
    command = "service {} {}".format(args[1], args[0])
    perform.execute(command, root=True)


def reinstall(args, noauth, yes):
    """
    Reinstall the given packages
    $ wajig reinstall <package name(s)>

    options:
      -n --noauth   reinstall even if package is untrusted
      -y --yes      install without (yes/no) prompts; use with care!

    note: this runs 'apt-get install --reinstall'
    """
    util.requires_args("reinstall", args, "a list of packages")
    command = "apt-get install --reinstall {} {} " + " ".join(args[1:])
    command = command.format(noauth, yes)
    perform.execute(command, root=True)


def show(args):
    """
    Provide a detailed description of package (describe -vv)
    $ wajig detail <package names>

    options:
      -f --fast     use apt-cache's version of SHOW, due to its speed; see
                    debian/changelog for 2.0.50 release for the rationale on
                    why aptitude's version was chosen as default
    """
    util.requires_args("show", args, "a list of packages or package file")
    package_names = " ".join(set(args[1:]))
    tool = "apt-cache" if util.fast else "aptitude"
    command = "{} show {}".format(tool, package_names)
    perform.execute(command)


def sizes(args):
    """
    Display installed sizes of given packages
    $ wajig sizes [<package name(s)>]

    Display installed sizes of all packages
    $ wajig sizes
    """
    packages = args[1:]

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
            if package_size and int(package_size) > 0:
                if package_name not in size_list:
                    size_list[package_name] = package_size
                    status_list[package_name] = package_status

    packages = list(size_list)
    packages.sort(key=lambda x: int(size_list[x]))  # sort by size

    if len(packages) == 0:
        print("No packages found from those known to be available or installed")
    else:
        print("{:<33} {:^10} {:>12}".format("Package", "Size (KB)", "Status"))
        print("{}-{}-{}".format("="*33, "="*10, "="*12))
        for package in packages:
            print("{:<33} {:^10} {:>12}".format(package,
                    format(int(size_list[package]), ',d'), status_list[package]))


def snapshot(args):
    """
    Generates a list of package=version for all installed packages
    $ wajig snapshot
    """
    util.requires_no_args(args[0], args)
    util.do_status([], snapshot=True)


def source(args):
    """
    Retrieve and unpack sources for the named packages.
    $ wajig source

    note: this runs 'apt-get source'
    """
    util.requires_args(args[0], args, "a list of package names")
    util.requires_package("dpkg-source", "/usr/bin/dpkg-source")
    perform.execute("apt-get source " + " ".join(args[1:]))


def status(args):
    """
    Show the version and available versions of packages
    $ wajig status
    """
    util.do_status(args[1:])


def statusmatch(args):
    """
    Show the version and available versions of matching packages
    $ wajig status-search
    """
    util.requires_one_arg(args[0], args,
                         "a search string for the package name")
    try:
        packages = [s.strip() for s in
                    util.do_listnames(args[1:], pipe=True).readlines()]
    except AttributeError:
        print("No packages found matching '{0}'".format(args[1]))
    else:
        util.do_status(packages)


def syslog(args):
    """
    Display APT log file
    $ wajig list-log

    note: this runs 'cat /var/log/apt/history.log'
    """
    util.requires_no_args("syslog", args)
    perform.execute("cat /var/log/apt/history.log")


def tasksel(args):
    """
    Run the task selector to install groups of packages
    $ wajig tasksel

    note: this runs 'tasksel'
    """
    util.requires_no_args(args[0], args)
    util.requires_package("tasksel", "/usr/bin/tasksel")
    perform.execute("tasksel", root=True)


def toupgrade(args):
    """
    List packages with newer versions available for upgrading
    $ wajig toupgrade
    """
    util.requires_no_args(args[0], args)

    # A simple way of doing this is to just list packages in the installed
    # list and the available list which have different versions.
    # However this does not capture the situation where the available
    # package version predates the installed package version (e.g,
    # you've installed a more recent version than in the distribution).
    # So now also add in a call to "dpkg --compare-versions" which slows
    # things down quite a bit!

    # List each upgraded pacakge and it's version.
    to_upgrade = changes.get_to_upgrade()
    to_upgrade.sort()
    if to_upgrade:
        print("%-24s %-24s %s" % ("Package", "Available", "Installed"))
        print("="*24 + "-" + "="*24 + "-" + "="*24)
        for i in range(0, len(to_upgrade)):
            print("%-24s %-24s %-24s" % (to_upgrade[i],
                   changes.get_available_version(to_upgrade[i]),
                   changes.get_installed_version(to_upgrade[i])))
    else:
        print("No upgradeable packages")


def tutorial(args):
    """
    Display wajig tutorial
    $ wajig tutorial
    """
    util.requires_no_args("documentation", args)
    with open("/usr/share/wajig/help/TUTORIAL") as f:
        for line in f:
            print(line, end="")


def unhold(args):
    """
    Remove listed packages from hold so they are again upgradeable
    $ wajig unhold <package name>
    """
    util.requires_args(args[0], args, "a list of packages to remove from hold")
    packages = args[1:]
    for package in packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then.
        command = "echo \"" + package + " install\" | dpkg --set-selections"
        perform.execute(command, root=1)
    print("The following packages are still on hold:")
    perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")



def unofficial(args):
    """
    Search for an unofficial Debian package at apt-get.org
    $ wajig <package name>
    """
    util.requires_one_arg("unofficial", args, "one package name")
    util.requires_package("wget", "/usr/bin/wget")
    util.requires_package("fping", "/usr/bin/fping")
    package = args[1]
    if util.ping_host("www.apt-get.org"):

        print("Lines suitable for /etc/apt/sources.list")
        sys.stdout.flush()

        # Obtain the information from the Apt-Get server
        results = tempfile.mkstemp()[1]
        command = "wget --timeout=60 --output-document=" + results +\
                  " http://www.apt-get.org/" +\
                  "search.php\?query=" + package +\
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


def update(args):
    """
    Update the list of new and updated packages
    $ wajig update
    """
    util.requires_no_args(args[0], args)
    util.do_update()


def updateavailable(args):
    """
    note: this is for internal testing
    """
    util.requires_no_args(args[0], args)
    changes.update_available()


def upgrade(args, yes, noauth):
    """
    Conservative system upgrade... won't remove or install new packages
    $ wajig upgrade

    options:
      -b --backup   backup packages about to be upgraded onto some default directory
      -n --noauth   skip the authentication verification prompt before the upgrade
      -y --yes      purge without (yes/no) prompts; use with care!
    """
    util.requires_no_args("upgrade", args)
    packages = util.upgradable()
    if packages:
        if backup:
            util.requires_package("dpkg-repack", "/usr/bin/dpkg-repack")
            util.requires_package("fakeroot", "/usr/bin/fakeroot")
            changes.backup_before_upgrade(packages)
        command = "apt-get {0} {1} --show-upgraded upgrade".format(yes, noauth)
        perform.execute(command, root=True)
    else:
        print('No upgradeable packages. Did you run "wajig update" first?')


def verify(args):
    """
    Check package md5sum
    $ wajig verify <package name(s)>
    """
    util.requires_one_arg("verify", args, "a package name")
    util.requires_package("debsums", "/usr/bin/debsums")
    perform.execute("debsums " + args[1])


def versions(args):
    """
    List version and distribution of given packages:
    $ wajig versions <package name(s)>

    note: this runs 'apt-show-versions'
    """
    util.requires_package("apt-show-versions", "/usr/bin/apt-show-versions")
    packages = args[1:]
    if packages:
        for package in packages:
            perform.execute("apt-show-versions " + package)
    else:
        perform.execute("apt-show-versions")


def whichpackage(args):
    """
    Search for files matching a given pattern within packages
    $ wajig filesearch <pattern>

    note: if the file is not found, an attempt is made in apt-file's repository
    """
    util.requires_one_arg("whichpackage", args, "a file name")
    out = subprocess.getstatusoutput("dpkg --search " + args[1])
    if out[0]:  # didn't find matching package, so use the slower apt-file
        util.requires_package("apt-file", "/usr/bin/apt-file")
        perform.execute("apt-file search " + args[1])
    else:
        print(out[1])

