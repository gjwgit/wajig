# This file is part of wajig.  The copyright file is at debian/copyright.

"""Implementation of all COMMANDs"""

# Do not include any function in here that does not correspond to a COMMAND

import os
import re
import sys
import string
import random
import inspect
import tempfile
import subprocess
import urllib.request
import webbrowser
import shutil

import apt

# wajig modules
import wajig.perform as perform
import wajig.util as util
import wajig.debfile as debfile

from wajig.constants import APP, VERSION

# before we do any other command make sure the right files exist
util.ensure_initialised()

NO_UPGRADES = 'No packages need to be upgraded. Run "wajig update" to update from the repository.'


def addcdrom(args):
    """Add a Debian CD/DVD to APT's list of available sources"""
    perform.execute("/usr/bin/apt-cdrom add", root=True, teach=args.teach, noop=args.noop)


def addrepo(args):
    """Add a Launchpad PPA (Personal Package Archive) repository

    An example that shows how to add the daily builds of
    Google's Chromium browser:

    $ wajig addrepo ppa:chromium-daily
    """
    util.requires_package("add-apt-repository")
    perform.execute("/usr/bin/add-apt-repository " + args.ppa, root=True, teach=args.teach, noop=args.noop)

# ADDUSER

def adduser(args):
    """Add new user, multiple users, or as listed in a file.

With just a username create a new password while adding user and 
return that.

  $ wajig adduser fred

If a number is provided then that many new users are created and
the output will be username:password.

  $ wajig adduser 5
"""
    number = args.number
    username = args.username

    if number and not re.match(r"^[0-9]+$", number):
        username.insert(0, number)
        number = ""

    if number and username:
        print("wajig adduser: error: if a number is supplied " +
              "then no usernames allowed.")
        return()

    elif args.file:
        if not os.path.exists(args.file):
            print(f"wajig adduser: error: file not found '{args.file}'")
        elif not os.access(args.file, os.R_OK):
            print(f"wajig adduser: error: file not accessible '{args.file}'.")
        else:
            usernames = []
            for l in open(args.file, 'r'):
                usernames.append(l.strip())
    
    elif number and re.match(r"^[0-9]+$", number):
        usernames = []
        for i in range(int(number)):
            code = ''.join(random.choice(string.ascii_lowercase) for _ in range(7))
            usernames.append(f"u{code}")
            
    else:
        for u in username:
            if not re.match(r"^[a-z][-a-z0-9_]*$", u):
                print(f"wajig adduser: error: bad user name '{u}' " +
                      f"must start with lowercase then",
                      f"alphanumerics or underscore.")
        usernames = username

    util.requires_package("pwgen")
    created = []
    for u in usernames:
        command = f'adduser {u} --gecos "" --disabled-password'
        perform.execute(command, root=True, teach=args.teach, noop=args.noop)
        
        command = f"pwgen 16 1"
        password = perform.execute(command, pipe=True, teach=args.teach, noop=args.noop)
        if password: password = password.readline().strip()
        
        command = f'echo "{u}:{password}" | sudo chpasswd'
        perform.execute(command, root=True, teach=args.teach, noop=args.noop)

        print()
        created.append(f"{u}:{password}")

    print("\n".join(created))
            
def aptlog(args):
    """Display APT log file"""
    perform.execute("cat /var/log/apt/history.log")


def autoalts(args):
    """Mark the Alternative to be auto-set (using set priorities)"""
    perform.execute(
        "/usr/bin/update-alternatives --auto " + args.alternative, root=True, teach=args.teach, noop=args.noop
    )


def autodownload(args):
    """Do an update followed by a download of all updated packages"""
    util.do_update(args.noop)
    command = ("/usr/bin/apt-get --download-only --show-upgraded --assume-yes "
               "--force-yes dist-upgrade")
    perform.execute(command, root=True)
    if not args.noop:
        upgradable_packages = util.upgradable()
        if upgradable_packages:
            util.do_describe(upgradable_packages, args.verbose)
        else:
            print("no upgradable packages")
        util.show_package_versions()


def autoclean(args):
    """Remove no-longer-downloadable .deb files from the download cache"""
    perform.execute("/usr/bin/apt-get autoclean", root=True, teach=args.teach, noop=args.noop)


def autoremove(args):
    """Remove unused dependency packages"""
    perform.execute("/usr/bin/apt autoremove", root=True, log=True, teach=args.teach, noop=args.noop)


def build(args):
    """Get source packages, unpack them, and build binary packages from them.

    Note: This also installs the needed build-dependencies if needed
    """
    util.requires_package("sudo")
    # First make sure dependencies are met
    if not builddeps(args):
        command = "apt-get {} source --build " + " ".join(args.packages)
        command = command.format(args.noauth)
        perform.execute(command)


def builddeps(args):
    """Install build-dependencies for given packages"""
    command = "/usr/bin/apt-get {} {} build-dep " + " ".join(args.packages)
    command = command.format(args.yes, args.noauth)
    return perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def changelog(args):
    """Display Debian changelog of a package

    network on:
         changelog - if there's newer entries, display them
      -v changelog - if there's newer entries, display them, and proceed to
                     display complete local changelog

    network off:
         changelog - if there's newer entries, mention failure to retrieve
      -v changelog - if there's newer entries, mention failure to retrieve, and
                     proceed to display complete local changelog
    """

    package = util.package_exists(apt.Cache(), args.package)
    changelog = "{:=^79}\n".format(" {} ".format(args.package))  # header

    try:
        changelog += package.get_changelog()
    except AttributeError:
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
                try:
                    print(line, end="")
                except BrokenPipeError:
                    return

# CLEAN

def clean(args):
    """Remove all deb files from the download cache"""
    perform.execute("/usr/bin/apt-get clean", root=True, teach=args.teach, noop=args.noop)

# COMMANDS

def commands(args, result=False):
    """Display all wajig commands"""
    cmds = []
    for name, value in sorted(globals().items()):
        if inspect.isfunction(value):
            if result:
                cmds.append(name)
            else:
                summary = value.__doc__.split('\n')[0]
                if args.pattern:
                    if args.pattern not in summary and \
                       args.pattern not in name:
                        continue
                print(f"{name:<18} {summary}")
    if result: return cmds

def contents(args):
    """List the contents of a package file (.deb)"""
    perform.execute("dpkg --contents " + args.debfile, teach=args.teach, noop=args.noop)


def dailyupgrade(args):
    """Perform an update then a dist-upgrade"""
    util.do_update(args.noop)
    perform.execute("/usr/bin/apt --show-upgraded dist-upgrade",
                    root=True, log=True, teach=args.teach, noop=args.noop)

# DELUSER

def deluser(args):
    """Delete user accounts

With a list of usernames, delete each user.

  $ wajig deluser fred susan
"""
    for u in args.username:
        command = f"sudo deluser --remove-home --backup {u}"
        perform.execute(command, root=True, teach=args.teach, noop=args.noop)
        if not u == args.username[-1]: print()


def dependents(args):
    """Display packages which have some form of dependency on the given package

    Types of dependencies:
    * Depends
    * Recommends
    * Suggests
    * Replaces
    * Enhances
    """

    DEPENDENCY_TYPES = [
        "Depends",
        "Recommends",
        "Suggests",
        "Replaces",
        "Enhances",
    ]

    cache = apt.cache.Cache()
    package = util.package_exists(cache, args.package)
    dependents = {name : [] for name in DEPENDENCY_TYPES}

    for key in cache.keys():
        other_package = cache[key]
        for dependency_type, specific_dependents in dependents.items():
            if package.shortname in \
            util.extract_dependencies(other_package, dependency_type):
                specific_dependents.append(other_package.shortname)

    for dependency_type, specific_dependents in dependents.items():
        if specific_dependents:
            print("{}: {}".format(
                dependency_type.upper(), " ".join(specific_dependents)
            ))


def describe(args):
    """Display one-line descriptions for the given packages"""
    util.do_describe(args.packages, args.verbose)



def describenew(args):
    """Display one-line descriptions of newly-available packages

    This produces the same output as 'wajig new'
    """
    util.newly_available()


def distupgrade(args):
    """Comprehensive system upgrade

    This may remove some packages in order to ensure no package is
    left stale. Use the more conservative 'upgrade' command to avoid
    that.
    """
    packages = util.upgradable(distupgrade=True)
    if not packages and not args.dist:
        print(NO_UPGRADES)
        return
    if args.backup:
        util.requires_package("dpkg-repack")
        util.requires_package("fakeroot")
        util.backup_before_upgrade(packages, distupgrade=True)
    cmd = "/usr/bin/apt --show-upgraded {} {} {} ".format(
        args.local, args.yes, args.noauth
    )
    if args.dist:
        cmd += "--target-release " + args.dist + " "
    cmd += "full-upgrade"
    perform.execute(cmd, root=True, log=True, teach=args.teach, noop=args.noop)


def download(args):
    """Download one or more packages without installing them"""
    print("Packages being downloaded to /var/cache/apt/archives/")
    command = "/usr/bin/apt-get --reinstall --download-only install "
    packages = util.consolidate_package_names(args)
    command = command + " ".join(packages)
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)


def editsources(args):
    """Edit list of Debian repository locations for packages"""
    perform.execute("/usr/bin/apt edit-source", root=True, teach=args.teach, noop=args.noop)


def extract(args):
    """Extract the files from a package file to a directory"""
    command = "dpkg --extract {} {}"
    command = command.format(args.debfile, args.destination_directory)
    perform.execute(command, teach=args.teach, noop=args.noop)


def fixconfigure(args):
    """Fix an interrupted install"""
    perform.execute("/usr/bin/dpkg --configure --pending", root=True, teach=args.teach, noop=args.noop)


def fixinstall(args):
    """Fix an install interrupted by broken dependencies"""
    command = "/usr/bin/apt-get --fix-broken {} install".format(args.noauth)
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def fixmissing(args):
    """Fix and install even though there are missing dependencies"""
    command = "/usr/bin/apt-get --ignore-missing {} upgrade".format(args.noauth)
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def force(args):
    """Install packages and ignore file overwrites and depends

    Note: This is useful when there is a conflict of the same file from
          multiple packages or when a dependency is not installed for
          whatever reason
    """

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
            lscmd = "ls {} | grep -E '^{}_' | sort -k 1b,1 | tail -n -1"
            lscmd = lscmd.format(archives, package)
            matches = perform.execute(lscmd, pipe=True)
            debpkg = matches.readline().strip()

            if not debpkg:
                dlcmd = (
                    "apt-get --quiet=2 --reinstall --download-only "
                    "install '{}'"
                ).format(package)
                perform.execute(dlcmd, root=True)
                matches = perform.execute(lscmd, pipe=True)
                debpkg = matches.readline().strip()

            # Force install the package from the download archive.
            command += "'" + archives + debpkg + "' "

    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def hold(args):
    """Place packages on hold (so they will not be upgraded)"""
    for package in args.packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then!
        command = '/bin/echo "{} hold" | /usr/bin/dpkg --set-selections'
        perform.execute(command.format(package), root=True, teach=args.teach, noop=args.noop)
    print("The following packages are on hold:")
    perform.execute("dpkg --get-selections | grep -E 'hold$' | cut -f1", teach=args.teach, noop=args.noop)


def info(args):
    """List the information contained in a package file"""
    perform.execute("dpkg --info " + args.package, teach=args.teach, noop=args.noop)


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
    'a', 'b', and 'c''
    """

    packages = util.consolidate_package_names(args)

    online_files = [
        package for package in packages if
        package.startswith(("http://", "ftp://"))
    ]
    deb_files = list()
    for package in online_files:
        if not package.endswith(".deb"):
            print("A valid .deb file should have a '.deb' extension")
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

    deb_files.extend([
        package for package in packages if package.endswith(".deb")
        and os.path.exists(package)
    ])
    if deb_files:
        debfile.install(deb_files)

    packages = packages.difference(online_files, deb_files)
    if packages:
        if args.dist:
            args.dist = "--target-release " + args.dist
        command = "/usr/bin/apt {} {} {} {} --auto-remove install "
        command += " ".join(packages)
        command = command.format(args.yes, args.noauth, args.recommends,
                                 args.dist)
        perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


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
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def integrity(args):
    """Check the integrity of installed packages (through checksums)"""
    util.requires_package("debsums")
    perform.execute("debsums --all --silent", teach=args.teach, noop=args.noop)


def large(args):
    """List size of all large (>10MB) installed packages"""
    util.sizes(size=10000)


def lastupdate(args):
    """Identify when an update was last performed"""
    command = ("ls -l --full-time " + util.available_file + " 2> "
               "/dev/null | awk '{printf \"Last update was %s %s %s\\n\""
               ", $6, $7, $8}' | sed 's|\.000000000||'")
    perform.execute(command, teach=args.teach, noop=args.noop)


def listall(args):
    """List one line descriptions for all packages"""
    command = ("apt-cache dumpavail |"
               "grep -E \"^(Package|Description): \" |"
               "awk '/^Package: /{pkg=$2} /^Description: /"
               "{printf(\"%-24s %s\\n\", pkg,"
               "substr($0,13))}' | sort -u -k 1b,1")
    if args.pattern:
        command = "{} | grep -E '{}'".format(command, args.pattern)
    perform.execute(command, teach=args.teach, noop=args.noop)



def listcache(args):
    """List the contents of the download cache"""
    command = "printf 'Found %d files %s in the cache.\n\n'\
           $(ls /var/cache/apt/archives/ | wc -l) \
           $(ls -sh /var/cache/apt/archives/ | head -1 | awk '{print $2}')"
    perform.execute(command)
    command = "ls /var/cache/apt/archives/"
    if args.pattern:
        command = "{} | grep -E '{}'".format(command, args.pattern)
    perform.execute(command, teach=args.teach, noop=args.noop)


def listalternatives(args):
    """List the objects that can have alternatives configured"""
    command = ("ls /etc/alternatives/ | "
               "grep -E -v '(\.1|\.1\.gz|\.8|\.8\.gz|README)$'")
    perform.execute(command, teach=args.teach, noop=args.noop)


def listdaemons(args):
    """List the daemons that wajig can start, stop, restart, or reload"""
    util.requires_package("chkconfig")
    perform.execute("chkconfig", teach=args.teach, noop=args.noop)


def listfiles(args):
    """List the files that are supplied by the named package"""
    if args.package.endswith(".deb"):
        perform.execute("dpkg --contents " + args.package, teach=args.teach, noop=args.noop)
        return
    try:
        output = perform.execute(
            "dpkg --listfiles " + args.package, getoutput=True, teach=args.teach, noop=args.noop
        )
    except subprocess.CalledProcessError:
        if shutil.which("apt-file"):
            perform.execute("apt-file list --regexp ^{}$".format(args.package), teach=args.teach, noop=args.noop)
    else:
        for line in output.decode().strip().split('\n'):
            print(line)


def listhold(args):
    """List packages that are on hold (i.e. those that won't be upgraded)"""
    perform.execute("dpkg --get-selections | grep -E 'hold$' | cut -f1", teach=args.teach, noop=args.noop)


def listinstalled(args):
    """List installed packages"""
    command = "dpkg --get-selections | cut -f1"
    if args.pattern:
        command += " | grep -E '{}' | sort -k 1b,1".format(args.pattern)
    perform.execute(command, teach=args.teach, noop=args.noop)


def listlog(args):
    """Display wajig log file"""
    perform.execute("cat " + util.log_file, teach=args.teach, noop=args.noop)

# LISTNAMES

def listnames(args):
    """List all known packages; optionally filter the list with a pattern"""
    util.do_listnames(args.pattern)

# LISTPACKAGES

def listpackages(args):
    """List the status, version, and description of installed packages"""
    command = "dpkg --list '*' | grep -E -v 'no description avail'"
    if args.pattern:
        command += " | grep -E '{}' | sort -k 1b,1".format(args.pattern)
    perform.execute(command, teach=args.teach, noop=args.noop)


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
                perform.execute(command, teach=args.teach, noop=args.noop)
    else:
        root = "/var/lib/dpkg/info/"
        for script in scripts:
            fname = root + package + "." + script
            if os.path.exists(fname):
                nlen = int((72 - len(script))/2)
                print(">"*nlen, script, "<"*nlen)
                perform.execute("cat " + fname, teach=args.teach, noop=args.noop)


def listsection(args):
    """List packages that belong to a specific section

    Note: Use the LISTSECTIONS command for a list of Debian Sections
    """
    cache = apt.cache.Cache()
    for package in cache.keys():
        package = cache[package]
        if package.section == args.section:
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
    perform.execute(command, teach=args.teach, noop=args.noop)


def localupgrade(args):
    """Upgrade using only packages that are already downloaded"""
    command = (
        "/usr/bin/apt-get --no-download --ignore-missing "
        "--show-upgraded upgrade"
    )
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def madison(args):
    """Runs the madison command of apt-cache"""
    command = "apt-cache madison " + " ".join(set(args.packages))
    perform.execute(command, teach=args.teach, noop=args.noop)


def move(args):
    """Move packages in the download cache to a local Debian mirror"""
    util.requires_package("apt-move")
    perform.execute("/usr/bin/apt-move update", root=True, teach=args.teach, noop=args.noop)


def new(args):
    """Display newly-available packages"""
    util.newly_available(args.verbose)


def newdetail(args):
    """Display detailed descriptions of newly-available packages

    This produces the same output as 'wajig new --verbose'
    """
    util.newly_available(verbose=True)


def news(args):
    """Display the NEWS file of a given package"""
    util.display_sys_docs(args.package, "NEWS.Debian NEWS".split())


def nonfree(args):
    """List packages that don't meet the Debian Free Software Guidelines"""
    util.requires_package("vrms")
    perform.execute("vrms", teach=args.teach, noop=args.noop)


def orphans(args):
    """List libraries not required by any installed package """
    util.requires_package("deborphan")
    perform.execute("deborphan", teach=args.teach, noop=args.noop)

# PASSWORD
    
def password(args):
    """Generate a good password optionally with punctuation

Default is to generate one password.

Simple usage to generate a list of 5 passwords of length 20 with 
special characters (punctuation).:

  $ wajig password --punct 5 20
"""
    length = args.length if args.length else 16
    number = args.number if args.number else 1
    if args.punct:
        command = f"cat /dev/urandom | tr -cd '[:graph:]' | head -c {length}; echo"
        perform.execute(command, teach=args.teach, noop=args.noop)
        if not args.noop:
            for i in range(1, int(number)):
                perform.execute(command)
    else:
        util.requires_package("pwgen")
        command = f"pwgen {length} {number} | tr ' ' '\n'"
        perform.execute(command, teach=args.teach, noop=args.noop)

# POLICY
    
def policy(args):
    """From preferences file show priorities/policy (available)"""
    perform.execute("apt-cache policy " + " ".join(args.packages), teach=args.teach, noop=args.noop)


def purge(args):
    """Remove one or more packages and their configuration files"""
    packages = util.consolidate_package_names(args)
    command = "/usr/bin/apt-get {} {} --auto-remove purge "
    command = command.format(args.yes, args.noauth)
    command = command + " ".join(packages)
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


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
        perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def purgeremoved(args):
    """Purge all packages marked as deinstall"""
    packages = ""
    cmd = (
        "dpkg-query --show "
        "--showformat='${Package}:${Architecture}\t${Status}\n' | "
        "grep -E \"deinstall ok config-files\" | cut -f 1 "
    )
    packages = perform.execute(cmd, pipe=True, teach=args.teach, noop=args.noop)
    if packages:
        packages = " ".join(packages)
        packages = " ".join(packages.split())
        perform.execute("/usr/bin/apt-get purge " + packages,
                        root=True, log=True, teach=args.teach, noop=args.noop)


def rbuilddeps(args):
    """Display the packages which build-depend on the given package"""
    util.requires_package("grep-dctrl")
    command = "grep-available -sPackage -FBuild-Depends,Build-Depends-Indep "
    command = command + args.package + " /var/lib/apt/lists/*Sources"
    perform.execute(command, teach=args.teach, noop=args.noop)


def readme(args):
    """Display the README file(s) of a given package

    This will display README, README.Debian, README.rst, and USAGE
    files of a package. It will also decompress them if they are
    postfixed with .gz.
    """
    matches = 'README README.Debian README.rst USAGE'
    util.display_sys_docs(args.package, matches.split())

# REBOOT 20200820 consider removal as also reported in SYSINFO
    
def reboot(args):
    """Check if a reboot is required"""

    REBOOT = "/var/run/reboot-required"
    PKGS = "/var/run/reboot-required.pkgs"
    cmd = f"test -f {REBOOT}"
    result = perform.execute(cmd)
    if result == 0:
        cmd = f"cat {REBOOT}"
        perform.execute(cmd)
        cmd = f"test -f {PKGS}"
        result = perform.execute(cmd)
        if result == 0:
            print("\nThe following packages necessitate the reboot:\n")
            cmd = f"cat {PKGS} | sort -u | perl -p -e 's|^|  |'"
            perform.execute(cmd)
            print()
        print('To reboot use "sudo reboot"')
    else:
        print('A reboot is not required.')

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

    command = "/usr/bin/apt-get --download-only --reinstall -u install {} {}"
    command = command.format(args.noauth, " ".join(package_names))
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)


def reconfigure(args):
    """Reconfigure package"""
    command = "/usr/sbin/dpkg-reconfigure " + " ".join(args.packages)
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)


def recommended(args):
    """Display packages installed as Recommends and have no dependents"""
    perform.execute(
        "aptitude search "
        "'?and( ?automatic(?reverse-recommends(?installed)), "
        "?not(?automatic(?reverse-depends(?installed))) )'", teach=args.teach, noop=args.noop
    )


def reinstall(args):
    """Reinstall the given packages"""
    command = "/usr/bin/apt install --reinstall {} {} {}"
    command = command.format(args.noauth, args.yes, " ".join(args.packages))
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def reload(args):
    """Reload system daemons (see LIST-DAEMONS for available daemons)"""
    command = "/usr/sbin/service {} reload".format(args.daemon)
    if perform.execute(command, root=True):
        print("attempt FORCE-RELOAD instead")
        command = "/usr/sbin/service {} force-reload ".format(args.daemon)
        perform.execute(command, root=True, teach=args.teach, noop=args.noop)


def remove(args):
    """Remove packages (see also PURGE command)"""
    packages = util.consolidate_package_names(args)
    command = "/usr/bin/apt {} {} --auto-remove remove " + " ".join(packages)
    command = command.format(args.yes, args.noauth)
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def removeorphans(args):
    """Remove orphaned libraries"""
    util.requires_package("deborphan")
    packages = ""
    for package in perform.execute("deborphan", pipe=True):
        packages += " " + package.strip()
    if packages:
        command = "/usr/bin/apt-get --auto-remove remove {} {}"
        command = command.format(args.yes, packages)
        perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


def repackage(args):
    """Generate a .deb file from an installed package"""
    util.requires_package("dpkg-repack")
    util.requires_package("fakeroot")
    command = "fakeroot --unknown-is-real dpkg-repack " + args.package
    perform.execute(command, teach=args.teach, noop=args.noop)


def reportbug(args):
    """Report a bug in a package using Debian BTS (Bug Tracking System)"""
    util.requires_package("reportbug", "/usr/bin/reportbug")
    perform.execute("reportbug " + args.package, teach=args.teach, noop=args.noop)


def restart(args):
    """Restart system daemons (see LIST-DAEMONS for available daemons)"""
    command = "/usr/sbin/service {} restart".format(args.daemon)
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)


def rpm2deb(args):
    """Convert an .rpm file to a Debian .deb file"""
    command = "alien " + args.rpm
    perform.execute(command, teach=args.teach, noop=args.noop)


def rpminstall(args):
    """Install an .rpm package file"""
    command = "/usr/bin/alien --install " + args.rpm
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)


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
        command = "apt --names-only search {}"
        command = command.format(" ".join(args.patterns))
    elif args.verbose == 1:
        import shlex
        args.patterns = [shlex.quote(pattern) for pattern in args.patterns]
        command = "apt-cache search {} | grep -E --ignore-case '{}'"
        command = command.format(" ".join(args.patterns),
                                 "\|".join(args.patterns))
    else:
        command = "apt-cache search --full " + " ".join(args.patterns)
    perform.execute(command, teach=args.teach, noop=args.noop)


def searchapt(args):
    """Find nearby Debian package repositories"""
    util.requires_package("netselect-apt")
    command = "netselect-apt " + args.dist
    perform.execute(command, teach=args.teach, noop=args.noop)

# SHOW

def show(args):
    """Provide a detailed description of package"""
    package_names = " ".join(set(args.packages))
    tool = "apt-cache" if args.fast else "apt"
    command = "{} show {}".format(tool, package_names)
    perform.execute(command, teach=args.teach, noop=args.noop)

# START

def start(args):
    """Start system daemons (see LIST-DAEMONS for available daemons)"""
    command = "/usr/sbin/service {} start".format(args.daemon)
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)

# STOP

def stop(args):
    """Stop system daemons (see LISTDAEMONS for available daemons)"""
    command = "/usr/sbin/service {} stop".format(args.daemon)
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)

# SIZES

def sizes(args):
    """Display installed sizes of given packages

    To display sizes of all packages, do not use any argument:
    $ wajig sizes
    """
    util.sizes(args.packages)

# SNAPSHOT

def snapshot(args):
    """Generates a list of package=version for all installed packages"""
    util.do_status([], snapshot=True)

# SOURCE

def source(args):
    """Retrieve and unpack sources for the named packages"""
    util.requires_package("dpkg-source")
    perform.execute("apt-get source " + " ".join(args.packages), teach=args.teach,
                    noop=args.noop)

# STATUS

def status(args):
    """Show the version and available versions of packages (with regexp support)"""
    pkgs = []
    regexp = set('.^$*+?{},\[]|()')
    for p in args.pattern:
        notregexp = not any((c in regexp for c in p))
        if notregexp:
            pkgs.append(p)
        else:
            try:
                fnd = [s.strip() for s in
                       util.do_listnames(p, pipe=True,
                                         teach=args.teach, noop=args.noop).readlines()]
                pkgs.extend(fnd)
            except AttributeError:
                pass
    util.do_status(pkgs)

# SYSINFO
        
def sysinfo(args):
    """Print information about your system"""

    # HOSTNAME
    
    command = "hostname"
    result  = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    print(f"Hostname:   {result}")

    # OS
    
    command = "cat /etc/*release | grep '^NAME=' | cut -d '\"' -f2"
    result  = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    command = "cat /etc/*release | grep '^VERSION=' | cut -d '\"' -f2"
    ver     = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    command = "uname -r"
    kernel  = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    print(f"OS:         {result} {ver} {kernel}")

    # COMPUTER
    
    file = "/var/log/kern.log"
    if os.path.isfile(file) and os.access(file, os.R_OK):
        command  = "zgrep DMI: /var/log/kern.log* | grep kernel: | "
        command += "uniq | sed 's|^.*DMI: ||' | head -1"
        result  = perform.execute(command, getoutput=True, teach=args.teach,
                                  noop=args.noop).decode("utf-8").strip()
        print(f"Computer:   {result}")
    else:
        print(f"Computer:   <{file} not accessible>")

    command = "cat /proc/cpuinfo | grep 'name'| uniq | sed 's|^model name	: ||'"
    result  = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    command = "cat /proc/cpuinfo | grep 'process'| wc -l"
    count   = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    command = "cat /proc/cpuinfo | grep bogomips | uniq | sed 's|bogomips\t:||'"
    bogomip = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    print(f"Processor:  {result} x {count} = {bogomip} bogomips")

    lspci = perform.execute("lspci|head -1", getoutput=True)
    if lspci:
        command  =  'GPU=$(lspci | grep VGA | cut -d ":" -f3); '
        command += 'RAM=$(cardid=$(lspci | grep VGA |cut -d " " -f1); '
        command += 'lspci -v -s $cardid | grep " prefetchable"| '
        command += 'cut -d "=" -f2 | tr -d "\]"); '
        command += 'echo $GPU $RAM'
        result  = perform.execute(command, getoutput=True, teach=args.teach,
                                  noop=args.noop).decode("utf-8").strip()
        print(f"Video:      {result}")

        command =  'lspci | grep "Audio device:" | sed "s|^.*Audio device: ||"'
        result  = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
        if result:
            print(f"Audio:      {result}")
        else:
            print(f"Audio:      <lspci found no audio device>")
    else:
        print("Video:      <lspci produces no output>")
        print("Audio:      <lspci produces no output>")
    
    command = "cat /proc/meminfo | grep MemTotal | awk '{print $2/(1024*1024)}'"
    result  = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    print(f"Memory:     {round(float(result))}GB RAM")

    # IP

    command = "/sbin/ifconfig | grep 'inet ' | awk '{print $2}'"
    localip = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip().split("\n")
    command = "wget http://ipinfo.io/ip -qO -"
    exterip = perform.execute(command, getoutput=True, teach=args.teach,
                              noop=args.noop).decode("utf-8").strip()
    print(f"IP:         {', '.join(localip)} (local) {exterip} (external)")
    
    # UPTIME
    
    command = "uptime --pretty"
    up  = perform.execute(command, getoutput=True, teach=args.teach,
                          noop=args.noop).decode("utf-8").strip()
    command = "uptime --since"
    since  = perform.execute(command, getoutput=True, teach=args.teach,
                             noop=args.noop).decode("utf-8").strip()
    print(f"Uptime:     {up} since {since}")

    # LOAD

    command = "uptime | perl -p -e 's|[^,]*, +||' | perl -p -e 's|  +| |g' | "
    command += "cut -d' ' -f2-"
    load  = perform.execute(command, getoutput=True, teach=args.teach,
                            noop=args.noop).decode("utf-8").strip()
    print(f"Load:       {load}")
    
    # REBOOT

    REBOOT = "/var/run/reboot-required"
    PKGS = "/var/run/reboot-required.pkgs"
    cmd = f"test -f {REBOOT}"
    result = perform.execute(cmd)
    reboot = "not required"
    if result == 0:
        reboot = "required"
        cmd = f"test -f {PKGS}"
        result = perform.execute(cmd)
        if result == 0:
            cmd = f"cat {PKGS} | sort -u"
            pkgs = perform.execute(cmd, getoutput=True, teach=args.teach,
                                   noop=args.noop).decode("utf-8").strip().split("\n")
            reboot += " for " + ", ".join(pkgs) + " updates"
    print(f"Reboot:     {reboot}")
    

# TASKSEL
    
def tasksel(args):
    """Run the task selector to install groups of packages"""
    util.requires_package("tasksel")
    perform.execute("/usr/bin/tasksel", root=True, log=True, teach=args.teach,
                    noop=args.noop)


def todo(args):
    """Display the TODO file of a given package"""
    util.display_sys_docs(args.package, ["TODO"])


def toupgrade(args):
    """List versions of upgradable packages"""
    if not util.show_package_versions():
        print("No upgradeable packages.")


def tutorial(args):
    """Display wajig tutorial"""
    perform.execute('zcat /usr/share/doc/wajig/TUTORIAL',
                    teach=args.teach, noop=args.noop)


def unhold(args):
    """Remove listed packages from hold so they are again upgradeable"""
    for package in args.packages:
        # The dpkg needs sudo but not the echo.
        # Do all of it as root then.
        command = "echo \"" + package + " install\" | dpkg --set-selections"
        perform.execute(command, root=True)
    print("The following packages are still on hold:")
    perform.execute("dpkg --get-selections | grep -E 'hold$' | cut -f1",
                    teach=args.teach, noop=args.noop)


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
    """Update the list of new and updated packages available from the repository"""
    util.do_update(args.noop)


def updatealternatives(args):
    """Update default alternative for things like x-window-manager"""
    command = "/usr/bin/update-alternatives --config " + args.alternative
    perform.execute(command, root=True, teach=args.teach, noop=args.noop)


def updatepciids(args):
    """Updates the local list of PCI ids from the internet master list"""
    util.requires_package("pciutils", path="/usr/bin/update-pciids")
    perform.execute("/usr/bin/update-pciids", root=True, teach=args.teach, noop=args.noop)


def updateusbids(args):
    """Updates the local list of USB ids from the internet master list"""
    util.requires_package("usbutils", path="/usr/sbin/update-usbids")
    perform.execute("/usr/sbin/update-usbids", root=True, teach=args.teach, noop=args.noop)


def upgrade(args):
    """Conservative system upgrade

    This will not go as far remove packages in order to fulfill the
    upgrade, so may leave stale packages around. Use 'dist-upgrade' to
    avoid that.
    """
    packages = util.upgradable()
    if packages:
        if args.backup:
            util.requires_package("dpkg-repack")
            util.requires_package("fakeroot")
            util.backup_before_upgrade(packages)
        command = (
            "/usr/bin/apt-get {} {} {} --show-upgraded --with-new-pkgs upgrade"
        )
        command = command.format(args.local, args.yes, args.noauth)
        perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)
    else:
        print(NO_UPGRADES)


def upgradesecurity(args):
    """Do a security upgrade"""
    sources_list = tempfile.mkstemp(".security", "wajig.", "/tmp")[1]
    sources_file = open(sources_list, "w")
    # check dist
    sources_file.write("deb http://security.debian.org/ " +\
                       "testing/updates main contrib non-free\n")
    sources_file.close()
    command = (
        "/usr/bin/apt-get --no-list-cleanup --option Dir::Etc::SourceList="
        "{} update"
    )
    command = command.format(sources_list)
    perform.execute(command, root=True)
    command = "/usr/bin/apt-get --option Dir::Etc::SourceList={} upgrade"
    command = command.format(sources_list)
    perform.execute(command, root=True, log=True, teach=args.teach, noop=args.noop)
    if os.path.exists(sources_list):
        os.remove(sources_list)


def verify(args):
    """Check package's md5sum"""
    util.requires_package("debsums")
    perform.execute("debsums " + args.package, teach=args.teach, noop=args.noop)

    
def version(args):
    """Report wajig version"""
    print(f"{APP} {VERSION}")


def versions(args):
    """List version and distribution of given packages"""
    util.requires_package("apt-show-versions")
    if args.packages:
        for package in args.packages:
            perform.execute("apt-show-versions " + package, teach=args.teach, noop=args.noop)
    else:
        perform.execute("apt-show-versions", teach=args.teach, noop=args.noop)


def whichpackage(args):
    """Search for files matching a given pattern within packages

    Note: also searches files for uninstalled packages if apt-file is
    installed
    """
    try:
        output = perform.execute(
            "dpkg --search " + args.pattern, getoutput=True, teach=args.teach, noop=args.noop
        ).decode()
    # 'dpkg --search' returns a failing error code if it does not find matches
    except subprocess.CalledProcessError:
        installed_matches = []
    else:
        installed_matches = output.strip().split('\n')
        header = "INSTALLED MATCHES (x{})".format(len(installed_matches))
        print(header)
        print('-' * len(header))
        for line in installed_matches:
            print(line)
        print()
    if shutil.which("apt-file"):
        try:
            output = perform.execute(
                "apt-file search " + args.pattern, getoutput=True
            ).decode()
            all_matches = output.strip()
            if all_matches:
                all_matches = all_matches.split('\n')
                uninstalled_matches = set(all_matches) - set(installed_matches)
                header = "UNINSTALLED MATCHES (x{})".format(
                    len(uninstalled_matches)
                )
                print(header)
                print('-' * len(header))
                for line in uninstalled_matches:
                    print(line)
        except subprocess.CalledProcessError as error:
            if error.returncode == 3:
                print("Cache found empty... be sure to run 'apt-file update'")
            else:
                print("No results found matching '{}'".format(args.pattern))
    else:
        print("NOTE: install apt-file in order to display uninstalled matches")
