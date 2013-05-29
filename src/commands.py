# This file is part of wajig.  The copyright file is at debian/copyright.

"""Implementation of all COMMANDs"""

# Do not include any function in here that does not correspond to a COMMAND

import os
import sys
import inspect
import tempfile
import subprocess
import urllib.request
import webbrowser

import apt

# wajig modules
import perform
import util
import debfile

# before we do any other command make sure the right files exist
util.ensure_initialised()


def addcdrom(args):
    """Add a Debian CD/DVD to APT's list of available sources"""
    perform.execute("/usr/bin/apt-cdrom add", root=True)


def addrepo(args):
    """Add a Launchpad PPA (Personal Package Archive) repository

    An example that shows how to add the daily builds of
    Google's Chromium browser:

    $ wajig addrepo ppa:chromium-daily"""
    util.requires_package("add-apt-repository")
    perform.execute("/usr/bin/add-apt-repository " + args.ppa, root=True)


def aptlog(args):
    """Display APT log file"""
    perform.execute("cat /var/log/apt/history.log")


def autoalts(args):
    """Mark the Alternative to be auto-set (using set priorities)"""
    perform.execute("/usr/sbin/update-alternatives --auto " + args.alternative,
                     root=True)


def autodownload(args):
    """Do an update followed by a download of all updated packages"""
    util.do_update(args.simulate)
    command = ("/usr/bin/apt-get --download-only --show-upgraded --assume-yes "
               "--force-yes dist-upgrade")
    perform.execute(command, root=True)
    if not args.simulate:
        upgradable_packages = util.upgradable()
        if upgradable_packages:
            util.do_describe(upgradable_packages, verbose)
        else:
            print("no upgradable packages")
        util.show_package_versions()


def autoclean(args):
    """Remove no-longer-downloadable .deb files from the download cache"""
    perform.execute("/usr/bin/apt-get autoclean", root=True)


def autoremove(args):
    """Remove unused dependency packages"""
    perform.execute("/usr/bin/apt-get autoremove", root=True)


def build(args):
    """Retrieve source packages, unpack them, and build binary (.deb) packages
    from them. This also installs the needed build-dependencies if needed."""
    util.requires_package("sudo")
    # First make sure dependencies are met
    command = "/usr/bin/apt-get {} {} build-dep " + " ".join(args.packages)
    command = command.format(args.yes, args.noauth)
    result = perform.execute(command, root=True)
    if not result:
        command = "/usr/bin/apt-get {} source --build " + " ".join(args.packages)
        command = command.format(args.noauth)
        perform.execute(command, root=True)


def builddeps(args):
    """Install build-dependencies for given packages"""
    command = "/usr/bin/apt-get {} {} build-dep " + " ".join(args.packages)
    command = command.format(args.yes, args.noauth)
    perform.execute(command, root=True)


def changelog(args):
    """Display Debian changelog of a package

    network on:
         changelog - if there's newer entries, display them
      -v changelog - if there's newer entries, display them, and proceed to
                     display complete local changelog

    network off:
         changelog - if there's newer entries, mention failure to retrieve
      -v changelog - if there's newer entries, mention failure to retrieve, and
                     proceed to display complete local changelog"""

    package = util.package_exists(apt.Cache(), args.package)
    changelog = "{:=^79}\n".format(" {} ".format(args.package))  # header

    try:
        changelog += package.get_changelog()
    except AttributeError as e:
        # This is caught so as to avoid an ugly python-apt trace; it's a bug
        # that surfaces when:
        # 1. The package is not available in the default Debian suite
        # 2. The suite the package belongs to is set to a pin of < 0
        print("If this package is not on your default Debian suite, " \
              "ensure that its APT pinning isn't less than 0.")
        return
    help_message = "\nTo display the local changelog, run:\n" \
                   "wajig changelog --verbose " + args.package
    if "Failed to download the list of changes" in changelog:
        if not args.verbose:
            changelog += help_message
        else:
            changelog += "\n"
    elif changelog.endswith("The list of changes is not available"):
        changelog += ".\nYou are likely running the latest version.\n"
        if not args.verbose:
            changelog += help_message
    if not args.verbose:
        print(changelog)
    else:
        tmp = tempfile.mkstemp()[1]
        with open(tmp, "w") as f:
            if package.is_installed:
                changelog += "{:=^79}\n".format(" local changelog ")
            f.write(changelog)
        if package.is_installed:
            command = util.local_changelog(args.package, tmp)
            if not command:
                return
            perform.execute(command)
        with open(tmp) as f:
            for line in f:
                print(line, end="")


def clean(args):
    """Remove all deb files from the download cache"""
    perform.execute("/usr/bin/apt-get clean", root=True)


def contents(args):
    """List the contents of a package file (.deb)"""
    perform.execute("dpkg --contents " + args.debfile)


def dailyupgrade(args):
    """Perform an update then a dist-upgrade"""
    util.do_update(args.simulate)
    perform.execute("/usr/bin/apt-get --show-upgraded dist-upgrade", root=True)


def dependents(args):
    """Display packages which have some form of dependency on the given package

    Types of dependencies:
    * Depends
    * Recommends
    * Suggests
    * Replaces
    * Enhances"""

    DEPENDENCY_TYPES = [
        "Depends",
        "Recommends",
        "Suggests",
        "Replaces",
        "Enhances",
    ]

    cache = apt.cache.Cache()
    package = util.package_exists(cache, args.package)
    dependents = { name : [] for name in DEPENDENCY_TYPES }

    for key in cache.keys():
        other_package = cache[key]
        for dependency_type, specific_dependents in dependents.items():
            if package.shortname in \
            util.extract_dependencies(other_package, dependency_type):
                specific_dependents.append(other_package.shortname)

    for dependency_type, specific_dependents in dependents.items():
        if specific_dependents:
            output = dependency_type.upper(), " ".join(specific_dependents)
            print("{}: {}".format(*output))


def describe(args):
    """Display one-line descriptions for the given packages"""
    util.do_describe(args.packages, args.verbose)



def describenew(args):
    """Display one-line descriptions of newly-available packages

    This produces the same output as 'wajig new'"""
    util.newly_available()


def distupgrade(args):
    """Complete system upgrade; this may remove some packages and install new
      ones; for a safer upgrade, use UPGRADE command"""
    packages = util.upgradable(distupgrade=True)
    if not packages and not args.dist:
        print('No upgrades. Did you run "wajig update" beforehand?')
        return
    if args.backup:
        util.requires_package("dpkg-repack")
        util.requires_package("fakeroot")
        util.backup_before_upgrade(packages, distupgrade=True)
    cmd = "/usr/bin/apt-get --show-upgraded {} {} {} ".format(args.local, args.yes,
                                                              args.noauth)
    if args.dist:
        cmd += "--target-release " + args.dist + " "
    cmd += "dist-upgrade"
    perform.execute(cmd, root=True)


def download(args):
    """Download one or more packages without installing them"""
    print("Packages being downloaded to /var/cache/apt/archives/")
    command = "/usr/bin/apt-get --reinstall --download-only install "
    packages = util.consolidate_package_names(args)
    command = command + " ".join(packages)
    perform.execute(command, root=True)


def editsources(args):
    """Edit list of Debian repository locations for packages"""
    perform.execute("/usr/bin/editor /etc/apt/sources.list", root=True)


def extract(args):
    """Extract the files from a package file to a directory"""
    command = "dpkg --extract {} {}"
    command = command.format(args.debfile, args.destination_directory)
    perform.execute(command)


def fixconfigure(args):
    """Fix an interrupted install"""
    perform.execute("/usr/bin/dpkg --configure --pending", root=True)


def fixinstall(args):
    """Fix an install interrupted by broken dependencies"""
    command = "/usr/bin/apt-get --fix-broken {} install".format(args.noauth)
    perform.execute(command, root=True)


def fixmissing(args):
    """Fix and install even though there are missing dependencies"""
    command = "/usr/bin/apt-get --ignore-missing {} upgrade".format(args.noauth)
    perform.execute(command, root=True)


def force(args):
    """Install packages and ignore file overwrites and depends

    note: This is useful when there is a conflict of the same file from
          multiple packages or when a dependency is not installed for
          whatever reason"""

    command = "/usr/bin/dpkg --install --force overwrite --force depends "
    archives = "/var/cache/apt/archives/"

    # For a .deb file we simply force install it.
    if args.packages[0].endswith(".deb"):
        for package in args.packages:
            if os.path.exists(package):
                command += "'" + package + "' "
            elif os.path.exists(archives + package):
                command += "'" + archives + package + "' "
            else:
                message = ("File {} not found. "
                           "Searched current directory and {}."
                           "Please confirm the location and try again.")
                print(message.format(package, archives))
                return()
    else:
        # Package names rather than a specific deb package archive
        # is expected.
        for package in args.packages:
            # Identify the latest version of the package available in
            # the download archive, if there is any there.
            lscmd = "ls " + archives
            lscmd += " | grep -E '^" + package + "_' | sort -k 1b,1 | tail -n -1"
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

    perform.execute(command, root=True)


def hold(args):
    """Place packages on hold (so they will not be upgraded)"""
    for package in args.packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then!
        command = "/bin/echo \"" + package + " hold\" | /usr/bin/dpkg --set-selections"
        perform.execute(command, root=True)
    print("The following packages are on hold:")
    perform.execute("dpkg --get-selections | grep -E 'hold$' | cut -f1")


def info(args):
    """List the information contained in a package file"""
    perform.execute("dpkg --info " + args.package)


def init(args):
    """Initialise or reset wajig archive files"""
    util.reset_files()


def install(args):
    """Package installer

    notes:
    * specifying a .deb file will also try to satisfy that deb's dependencies;
    * one can specify multiple files with --fileinput option
    * specifying a url will try fetch the file from the internet, and keep it
      in "~/.wajig/$HOSTNAME"

    example:
    $ wajig install a b_1.0_all.deb http://example.com/c_1.0_all.deb

    Assuming there's no errors, the command will install 3 packages named
    'a', 'b', and 'c''"""

    packages = util.consolidate_package_names(args)

    online_files = [package for package in packages
                            if package.startswith(("http://", "ftp://"))]
    deb_files = list()
    for package in online_files:
        if not package.endswith(".deb"):
            print("A valied .deb file should have a '.deb' extension")
            continue
        filename = os.path.join(util.init_dir, package.split("/")[-1])
        try:
            response = urllib.request.urlopen(package)
        except urllib.error.HTTPError as error:
            print("{}; is '{}' the correct url?".format(error.reason, package))
        else:
            with open(filename, "wb") as f:
                f.write(response.read())
            deb_files.append(filename)

    deb_files.extend([package for package in packages
                            if package.endswith(".deb")
                            and os.path.exists(package)])
    if deb_files:
        debfile.install(deb_files, args)

    packages = packages.difference(online_files, deb_files)
    if packages:
        if args.dist:
            args.dist = "--target-release " + args.dist
        command = "/usr/bin/apt-get {} {} {} {} --auto-remove install "
        command += " ".join(packages)
        command = command.format(args.yes, args.noauth, args.recommends,
                                 args.dist)
        perform.execute(command, root=True)


def installsuggested(args):
    """Install a package and its Suggests dependencies"""
    cache = apt.cache.Cache()
    package = util.package_exists(cache, args.package,
                                  ignore_virtual_packages=True)
    dependencies = list(util.extract_dependencies(package, "Suggests"))
    for n, dependency in enumerate(dependencies):
        dependencies[n] = util.package_exists(cache, dependency).shortname
    dependencies = " ".join(dependencies)
    command = "/usr/bin/apt-get {} {} {} --auto-remove install {} {}"
    command = command.format(args.recommends, args.yes, args.noauth,
                             dependencies, args.package)
    perform.execute(command, root=True)


def integrity(args):
    """Check the integrity of installed packages (through checksums)"""
    perform.execute("debsums --all --silent")


def large(args):
    """List size of all large (>10MB) installed packages"""
    util.sizes(size=10000)


def lastupdate(args):
    """Identify when an update was last performed"""
    command = ("ls -l --full-time " + util.available_file + " 2> "
               "/dev/null | awk '{printf \"Last update was %s %s %s\\n\""
               ", $6, $7, $8}' | sed 's|\.000000000||'")
    perform.execute(command)


def listall(args):
    """List one line descriptions for all packages"""
    command = ("apt-cache dumpavail |"
               "grep -E \"^(Package|Description): \" |"
               "awk '/^Package: /{pkg=$2} /^Description: /"
               "{printf(\"%-24s %s\\n\", pkg,"
               "substr($0,13))}' | sort -u -k 1b,1")
    if args.pattern:
        command = "{} | grep -E '{}'".format(command, args.pattern)
    perform.execute(command)



def listcache(args):
    """List the contents of the download cache"""
    command = "printf 'Found %d files %s in the cache.\n\n'\
           $(ls /var/cache/apt/archives/ | wc -l) \
           $(ls -sh /var/cache/apt/archives/ | head -1 | awk '{print $2}')"
    perform.execute(command)
    command = "ls /var/cache/apt/archives/"
    if args.pattern:
        command = "{} | grep -E '{}'".format(command, args.pattern)
    perform.execute(command)


def listalternatives(args):
    """List the objects that can have alternatives configured"""
    command = ("ls /etc/alternatives/ | "
               "grep -E -v '(\.1|\.1\.gz|\.8|\.8\.gz|README)$'")
    perform.execute(command)


def listcommands(args):
    """Display all wajig commands"""
    for name, value in sorted(globals().items()):
        if inspect.isfunction(value):
            summary = value.__doc__
            print("{}\n    {}\n".format(name.upper(), summary))


def listdaemons(args):
    """List the daemons that wajig can start, stop, restart, or reload"""
    command = ("printf 'Found %d daemons in /etc/init.d.\n\n' "
               "$(ls /etc/init.d/ | "
               "grep -E -v '(~$|README|-(old|dist)|\.[0-9]*$)' | wc -l)")
    perform.execute(command)
    command = ("ls /etc/init.d/ | "
               "grep -E -v '(~$|README|-(old|dist)|\.[0-9]*$)' |"
               "pr --columns=3 --omit-header")
    perform.execute(command)


def listfiles(args):
    """List the files that are supplied by the named package"""
    if args.package.endswith("deb"):
        perform.execute("dpkg --contents " + args.package)
    else:
        perform.execute("dpkg --listfiles " + args.package)


def listhold(args):
    """List packages that are on hold (i.e. those that won't be upgraded)"""
    perform.execute("dpkg --get-selections | grep -E 'hold$' | cut -f1")


def listinstalled(args):
    """List installed packages"""
    command = "dpkg --get-selections | cut -f1"
    if args.pattern:
        command += " | grep -E '{}' | sort -k 1b,1".format(args.pattern)
    perform.execute(command)


def listnames(args):
    """List all known packages; optionally filter the list with a pattern"""
    util.do_listnames(args.pattern)


def listpackages(args):
    """List the status, version, and description of installed packages"""
    command = "dpkg --list '*' | grep -E -v 'no description avail'"
    if args.pattern:
        command += " | grep -E '{}' | sort -k 1b,1".format(args.pattern)
    perform.execute(command)


def listscripts(args):
    """List the control scripts of the package of deb file"""
    package = args.debfile
    scripts = ["preinst", "postinst", "prerm", "postrm"]
    if package.endswith(".deb"):
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
    """List packages that belong to a specific section

    note: Use the LISTSECTIONS command for a list of Debian Sections"""
    section = args.section
    cache = apt.cache.Cache()
    for package in cache.keys():
        package = cache[package]
        if(package.section == args.section):
            print(package.name)


def listsections(args):
    """List all available sections"""
    cache = apt.cache.Cache()
    sections = list()
    for package in cache.keys():
        package = cache[package]
        sections.append(package.section)
    sections = set(sections)
    for section in sections:
        print(section)


def liststatus(args):
    """Same as list but only prints first two columns, not truncated"""
    command = "COLUMNS=400 "
    command += "dpkg --list '*' | grep -E -v 'no description avail'"
    command += " | awk '{print $1,$2}'"
    if args.pattern:
        command += " | grep -E '{}' | sort -k 1b,1".format(args.pattern)
    perform.execute(command)


def localdistupgrade(args):
    """Dist-upgrade using only packages that are already downloaded"""
    command = ("/usr/bin/apt-get --no-download --ignore-missing --show-upgraded "
               "dist-upgrade")
    perform.execute(command, root=True)


def localupgrade(args):
    """Upgrade using only packages that are already downloaded"""
    command = "/usr/bin/apt-get --no-download --ignore-missing --show-upgraded upgrade"
    perform.execute(command, root=True)


def madison(args):
    """Runs the madison command of apt-cache"""
    command = "apt-cache madison " + " ".join(set(args.packages))
    perform.execute(command)


def move(args):
    """Move packages in the download cache to a local Debian mirror (apt-move)"""
    perform.execute("/usr/bin/apt-move update", root=True)


def new(args):
    """Display newly-available packages"""
    util.newly_available(args.verbose)


def newdetail(args):
    """Display detailed descriptions of newly-available packages

    This produces the same output as 'wajig new --verbose'"""
    util.newly_available(verbose=True)


def news(args):
    """Display the NEWS file of a given package"""
    util.display_sys_docs(args.package, "NEWS.Debian NEWS".split())


def nonfree(args):
    """List packages that don't meet the Debian Free Software Guidelines"""
    util.requires_package("vrms")
    perform.execute("vrms")


def orphans(args):
    """List libraries not required by any installed package """
    util.requires_package("deborphan")
    perform.execute("deborphan")


def policy(args):
    """From preferences file show priorities/policy (available)"""
    perform.execute("apt-cache policy " + " ".join(args.packages))


def purge(args):
    """Remove one or more packages and their configuration files"""
    packages = util.consolidate_package_names(args)
    command = "/usr/bin/apt-get {} {} --auto-remove purge "
    command = command.format(args.yes, args.noauth)
    command = command + " ".join(packages)
    perform.execute(command, root=True)


def purgeorphans(args):
    """Purge orphaned libraries (not required by installed packages)"""
    # Deborphans does not require root, but dpkg does,
    # so build up the orphans list first, then pass that to dpkg.
    util.requires_package("deborphan")
    packages = ""
    for package in perform.execute("deborphan", pipe=True):
        packages += " " + package.strip()
    if packages:
        command = "/usr/bin/apt-get --auto-remove purge {} {}"
        command = command.format(args.yes, packages)
        perform.execute(command, root=True)


def purgeremoved(args):
    """Purge all packages marked as deinstall"""
    packages = ""
    cmd = ("dpkg-query --show --showformat='${Package}\t${Status}\n' | "
           "grep -E \"deinstall ok config-files\" | cut -f 1 ")
    packages = perform.execute(cmd, pipe=True)
    if packages:
        packages = " ".join(packages)
        packages = " ".join(packages.split())
        perform.execute("/usr/bin/apt-get purge " + packages, root=True)


def rbuilddeps(args):
    """Display the packages which build-depend on the given package"""
    util.requires_package("grep-dctrl")
    command = "grep-available -sPackage -FBuild-Depends,Build-Depends-Indep "
    command = command + args.package + " /var/lib/apt/lists/*Sources"
    perform.execute(command)


def readme(args):
    """Display the README file of a given package"""
    util.display_sys_docs(args.package, "README README.Debian USAGE".split())


def recdownload(args):
    """Download a package and all its dependencies"""

    package_names = list()

    cache = apt.cache.Cache()
    for package in args.packages:
        util.package_exists(cache, package)

    print("Calculating all dependencies...")
    for package in args.packages:
        package_names.extend(util.get_deps_recursively(cache, package, []))
    print("Packages to download to /var/cache/apt/archives:")
    for package in package_names:
        # We do this because apt-get install dont list the packages to
        # reinstall if they don't need to be upgraded
        print(package, end=' ')
    print()

    command = "/usr/bin/apt-get --download-only --reinstall -u install " + args.noauth
    command += " ".join(package_names)
    perform.execute(command, root=True)


def reconfigure(args):
    """Reconfigure package"""
    command = "/usr/sbin/dpkg-reconfigure " + " ".join(args.packages)
    perform.execute(command, root=True)


def recommended(args):
    """Display packages that were installed via Recommends dependency
    and have no dependents"""
    command = ("aptitude search '"
              "?and( ?automatic(?reverse-recommends(?installed)), "
              "?not(?automatic(?reverse-depends(?installed))) )'")
    perform.execute(command)


def reinstall(args):
    """Reinstall the given packages"""
    command = "/usr/bin/apt-get install --reinstall {} {} " + " ".join(args.packages)
    command = command.format(args.noauth, args.yes)
    perform.execute(command, root=True)


def reload(args):
    """Reload system daemons (see LIST-DAEMONS for available daemons)"""
    command = "/usr/sbin/service {} reload".format(args.daemon)
    if perform.execute(command, root=True):
        print("attempt FORCE-RELOAD instead")
        command = "/usr/sbin/service {} force-reload ".format(args.daemon)
        perform.execute(command, root=True)


def remove(args):
    """Remove packages (see also PURGE command)"""
    packages = util.consolidate_package_names(args)
    command = "/usr/bin/apt-get {} {}--auto-remove remove " + " ".join(packages)
    command = command.format(args.yes, args.noauth)
    perform.execute(command, root=True)


def removeorphans(args):
    """Remove orphaned libraries"""
    util.requires_package("deborphan")
    packages = ""
    for package in perform.execute("deborphan", pipe=True):
        packages += " " + package.strip()
    if packages:
        command = "/usr/bin/apt-get --auto-remove remove {} {}"
        command = command.format(args.yes, packages)
        perform.execute(command, root=True)


def repackage(args):
    """Generate a .deb file from an installed package"""
    util.requires_package("dpkg-repack")
    util.requires_package("fakeroot")
    command = "fakeroot --unknown-is-real dpkg-repack " + args.package
    perform.execute(command, root=False)


def reportbug(args):
    """Report a bug in a package using Debian BTS (Bug Tracking System)"""
    util.requires_package("reportbug", "/usr/bin/reportbug")
    perform.execute("reportbug " + args.package)


def restart(args):
    """Restart system daemons (see LIST-DAEMONS for available daemons)"""
    command = "/usr/sbin/service {} restart".format(args.daemon)
    perform.execute(command, root=True)


def rpm2deb(args):
    """Convert an .rpm file to a Debian .deb file"""
    command = "alien " + args.rpm
    perform.execute(command)


def rpminstall(args):
    """Install an .rpm package file"""
    command = "/usr/bin/alien --install " + args.rpm
    perform.execute(command, root=True)


def search(args):
    """Search for package names containing the given pattern

    If '::' is found in the search term, use a debtags search; example:

    $ wajig search implemented-in::python
    balazar - adventure/action game Balazar -- Arkanae II, reforged scepters
    compizconfig-settings-manager - Compizconfig Settings Manager
    ...
"""
    if len(args.patterns) == 1 and '::' in args.patterns[0]:
        util.requires_package('debtags')
        command = 'debtags search ' + args.patterns[0]
        if args.verbose:
            command += ' --full'
    elif not args.verbose:
        command = "apt-cache --names-only search {}"
        command = command.format(" ".join(args.patterns))
    elif args.verbose == 1:
        import shlex
        args.patterns = [shlex.quote(pattern) for pattern in args.patterns]
        command = "apt-cache search {} | grep -E --ignore-case '{}'"
        command = command.format(" ".join(args.patterns),
                                 "\|".join(args.patterns))
    else:
        command = "apt-cache search --full " + " ".join(args.patterns)
    perform.execute(command)


def searchapt(args):
    """Find nearby Debian archives that are suitable for
    /etc/apt/sources.list"""
    util.requires_package("netselect-apt")
    command = "netselect-apt " + args.dist
    perform.execute(command)


def show(args):
    """Provide a detailed description of package"""
    package_names = " ".join(set(args.packages))
    tool = "apt-cache" if args.fast else "aptitude"
    command = "{} show {}".format(tool, package_names)
    perform.execute(command)


def start(args):
    """Start system daemons (see LIST-DAEMONS for available daemons)"""
    command = "/usr/sbin/service {} start".format(args.daemon)
    perform.execute(command, root=True)


def stop(args):
    """Stop system daemons (see LISTDAEMONS for available daemons)"""
    command = "/usr/sbin/service {} stop".format(args.daemon)
    perform.execute(command, root=True)


def sizes(args):
    """Display installed sizes of given packages
    $ wajig sizes [<package name(s)>]

    Display installed sizes of all packages
    $ wajig sizes"""
    util.sizes(args.packages)


def snapshot(args):
    """Generates a list of package=version for all installed packages"""
    util.do_status([], snapshot=True)


def source(args):
    """Retrieve and unpack sources for the named packages"""
    util.requires_package("dpkg-source")
    perform.execute("apt-get source " + " ".join(args.packages))


def status(args):
    """Show the version and available versions of packages"""
    util.do_status(args.packages)


def statusmatch(args):
    """Show the version and available versions of matching packages"""
    try:
        packages = [s.strip() for s in
                    util.do_listnames(args.pattern, pipe=True).readlines()]
    except AttributeError:
        print("No packages found matching '{}'".format(args.pattern))
    else:
        util.do_status(packages)


def tasksel(args):
    """Run the task selector to install groups of packages"""
    util.requires_package("tasksel")
    perform.execute("/usr/bin/tasksel", root=True)


def todo(args):
    """Display the TODO file of a given package"""
    util.display_sys_docs(args.package, ["TODO"])


def toupgrade(args):
    """List versions of upgradable packages"""
    if not util.show_package_versions():
        print("No upgradeable packages")

def tutorial(args):
    """Display wajig tutorial"""
    split = os.path.split(__file__)
    filename = os.path.join(split[0], "TUTORIAL")
    with open(filename) as f:
        for line in f:
            print(line, end="")


def unhold(args):
    """Remove listed packages from hold so they are again upgradeable"""
    for package in args.packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then.
        command = "echo \"" + package + " install\" | dpkg --set-selections"
        perform.execute(command, root=1)
    print("The following packages are still on hold:")
    perform.execute("dpkg --get-selections | grep -E 'hold$' | cut -f1")


def unofficial(args):
    """Search for an unofficial Debian package at apt-get.org"""
    aptget_org = "http://www.apt-get.org"
    try:
        urllib.request.urlopen(aptget_org)
    except urllib.error.URLError as error:
        print("'{}' is unreachable".format(aptget_org))
    else:
        url = aptget_org + "/search/?query=" + args.package
        webbrowser.open(url)


def update(args):
    """Update the list of new and updated packages"""
    util.do_update(args.simulate)


def updatealternatives(args):
    """Update default alternative for things like x-window-manager"""
    command = "/usr/sbin/update-alternatives --config " + args.alternative
    perform.execute(command, root=True)


def updatepciids(args):
    """Updates the local list of PCI ids from the internet master list"""
    util.requires_package("pciutils", path="/usr/bin/update-pciids")
    perform.execute("/usr/bin/update-pciids", root=True)


def updateusbids(args):
    """Updates the local list of USB ids from the internet master list"""
    util.requires_package("usbutils", path="/usr/sbin/update-usbids")
    perform.execute("/usr/sbin/update-usbids", root=True)


def upgrade(args):
    """Conservative system upgrade... won't remove or install new packages"""
    packages = util.upgradable()
    if packages:
        if args.backup:
            util.requires_package("dpkg-repack")
            util.requires_package("fakeroot")
            util.backup_before_upgrade(packages)
        command = "/usr/bin/apt-get {} {} {} --show-upgraded upgrade"
        command = command.format(args.local, args.yes, args.noauth)
        perform.execute(command, root=True)
    else:
        print('No upgradeable packages. Did you run "wajig update" first?')


def upgradesecurity(args):
    """Do a security upgrade"""
    sources_list = tempfile.mkstemp(".security", "wajig.", "/tmp")[1]
    sources_file = open(sources_list, "w")
    # check dist
    sources_file.write("deb http://security.debian.org/ " +\
                       "testing/updates main contrib non-free\n")
    sources_file.close()
    command = ("/usr/bin/apt-get --no-list-cleanup --option Dir::Etc::SourceList="
               "{} update")
    command = command.format(sources_list)
    perform.execute(command, root=True)
    command = "/usr/bin/apt-get --option Dir::Etc::SourceList={} upgrade"
    command = command.format(sources_list)
    perform.execute(command, root=True)
    if os.path.exists(sources_list):
        os.remove(sources_list)


def verify(args):
    """Check package's md5sum"""
    util.requires_package("debsums")
    perform.execute("debsums " + args.package)


def versions(args):
    """List version and distribution of given packages"""
    util.requires_package("apt-show-versions")
    if args.packages:
        for package in args.packages:
            perform.execute("apt-show-versions " + package)
    else:
        perform.execute("apt-show-versions")


def whichpackage(args):
    """Search for files matching a given pattern within packages

    Note: if no match is found, the apt-file repository is checked"""
    try:
        out = perform.execute("dpkg --search " + args.pattern, getoutput=True)
    except subprocess.CalledProcessError:
        util.requires_package("apt-file")
        perform.execute("apt-file search " + args.pattern)
    else:
        try:
            print(out.decode().strip())
        # will get here when on --simulate mode
        except AttributeError:
            pass
