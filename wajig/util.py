# This file is part of wajig.  The copyright file is at debian/copyright.

"Contains miscellaneous utilities."

import os
import sys
import tempfile
import re
import socket
from datetime import datetime
import time

import apt
import apt_pkg

import wajig.perform as perform

from rapidfuzz import fuzz
from rapidfuzz import process as fuzzprocess


#------------------------------------------------------------------------
#
# LOCATIONS
#
# init_dir
#
#       Wajig can be run on several machines sharing the same home
#       directories (often through NFS) so we need to have host specific
#       status files. Make sure the directories exist.
#
#------------------------------------------------------------------------
init_dir = os.path.expanduser("~/.wajig/") + socket.gethostname()
if not os.path.exists(init_dir):
    os.makedirs(init_dir)
#
# Temporarily, remove old files from .wajig
# After a few versions remove this code.
#
tmp_dir = os.path.expanduser("~/.wajig")
if os.path.exists(tmp_dir + "/Available"):
    os.rename(tmp_dir + "/Available", init_dir + "/Available")
if os.path.exists(tmp_dir + "/Available.prv"):
    os.rename(tmp_dir + "/Available.prv", init_dir + "/Available.prv")
if os.path.exists(tmp_dir + "/Installed"):
    os.rename(tmp_dir + "/Installed", init_dir + "/Installed")

# 100104 Remove any old tmp files. Bug#563573
perform.execute("rm -f " + init_dir + "/tmp*")

# TODO 23 Aug 2003
#
# Perhaps the only file that wajig needs to cache itself is
# Available.prv - the other two can be generated dynamically.
# Installed is now like this. Available can be done.
# This would mean essentially half the space usage (Installed
# is quite small at 30K, while Available and Available.prv
# were 280K). This is significant for a user who manages
# many hosts.
#
# If this is the case, then don't worry about creating a host
# subdirectory in ~/.wajig.  Simply use host in filename,
# unless init_dir is used elsewhere?????? Perhaps keep as folder
# since tempfiles are created there.
#
# TODO Work to use bzip2 files for available and previous.
# Then bunzip2 to temporary files when needed!
# Disk usage goes from 274K to 83K.
new_file = init_dir + "/New"
if not os.path.exists(new_file):
    with open(new_file, 'w'):
        pass

available_file = init_dir + "/Available"
previous_file = init_dir + "/Available.prv"

# Set the temporary directory to the init_dir.
# Large files are not generally written there so should be okay.
tempfile.tempdir = init_dir


# -----------------------------------------------------------------------
# Fuzzy match helper
# -----------------------------------------------------------------------

def yes_or_no(msg, *params, yes=True):
    """Query yes or no with message.

    Args:
        msg (str): Message to be printed out.
        yes (bool): Indicates whether the default answer is yes or no.
    """

    print(msg.format(*params) + (" [Y/n]?" if yes else " [y/N]?"), end=" ")
    choice = input().lower()

    answer = True if yes else False

    if yes and choice == "n":
        answer = False

    if not yes and choice == "y":
        answer = True

    return answer



def find_best_match(misspelled, candidates):
    """Find the best matched word with <misspelled> in <candidates>."""

    return fuzzprocess.extractOne(misspelled,
                                  candidates,
                                  scorer=fuzz.ratio,
                                  score_cutoff=80)

def get_misspelled_command(command, available_commands):

    try:
        matched, score = find_best_match(command, available_commands)
        if matched != command:
            yes = yes_or_no(
                "The command '{}' is not supported.  Did you mean '{}'",
                command,
                matched,
                yes=True,
            )
            if yes:
                print()
                return matched
    except TypeError:
        return None


def get_misspelled_pkg(model):

    model_completion_list = get_model_completion_list()
    if len(model_completion_list) != 0:
        try:
            matched, score = find_best_match(model, model_completion_list)
            if matched != model:
                yes = yes_or_no(
                    "The package '{}' was not found.  Did you mean '{}'",
                    model,
                    matched,
                    yes=True,
                )
                if yes:
                    print()
                    return matched
        except TypeError:
            return None

#-----------------------------------------------------------------------

def newly_available(verbose=False):
    """display brand-new packages.. technically new package names"""
    with open(new_file) as f:
        packages = f.readlines()
        if verbose:
            for package in packages:
                perform.execute('aptitude show ' + package)
        else:
            do_describe([package.strip() for package in packages], die=False)


def update_available(noreport=False):
    """Generate current list of available packages, backing up the old list
    """

    if not os.path.exists(available_file):
        f = open(available_file, "w")
        f.close()

    temporary_file = tempfile.mkstemp()[1]

    os.rename(available_file, temporary_file)
    # sort --unique so packages with more that one architecture are included
    # only once. This makes the count shown by "update" consistent with the
    # output of "toupgrade", though not necessarily with the list shown
    # by "upgrade" (really "apt-get --show-upgraded upgrade"), which might
    # show amd64 and i386 versions.
    command = ("apt-cache dumpavail "
               "| egrep '^(Package|Version):' "
               "| tr '\n' ' '"
               "| perl -p -e 's|Package: |\n|g; s|Version: ||g'"
               "| sort -u -k 1b,1 | tail -n +2 | sed 's| $||' > ") \
                + available_file
    # Use langC in the following since it uses a grep.
    perform.execute(command, langC=True)  # root is not required.
    os.rename(temporary_file, previous_file)

    available_packages = open(available_file).readlines()
    previous_packages = open(previous_file).readlines()
    diff = len(available_packages) - len(previous_packages)

    temporary_file = tempfile.mkstemp()[1]
    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    command = "join -v 1 -t' '  {0} {1} | cut -d' ' -f 1 | tee {2} | wc -l"
    command = command.format(available_file, previous_file, temporary_file)
    newest = perform.execute(command, pipe=True, langC=True)
    newest = newest.readlines()[0].strip()

    if newest != "0":
        os.rename(temporary_file, new_file)
    else:
        os.remove(temporary_file)

    if not noreport:
        if diff < 0:
            direction = str(0 - diff) + " down on"
        elif diff == 0:
            direction = "the same as"
        else:
            direction = str(diff) + " up on"
        print("This is " + direction + " the previous count", end=' ')
        print("with " + newest + " new", end=' ')
        if newest == "1":
            print("package.")
        else:
            print("packages.")

def gen_installed_command_str():
    """Generate command to list installed packages and their status."""
    # Use sort --unique. See comment in update_available().
    command = ("cat /var/lib/dpkg/status | "
               "egrep '^(Package|Status|Version):' | "
               "awk '/^Package: / {pkg=$2} "
               "     /^Status: / {s1=$2;s2=$3;s3=$4}"
               "     /^Version: / {print pkg,$2,s1,s2,s3}' | "
               "grep 'ok installed' | awk '{print $1,$2}' | sort -u -k 1b,1")
    return command


def count_upgrades():
    """Return as a string the number of new upgrades since last update."""
    ifile = tempfile.mkstemp()[1]
    # Use langC in the following since it uses a grep.
    perform.execute(gen_installed_command_str() + " > " + ifile, langC=True)
    command = ("join %s %s |"
               "awk '$2 != $3 {print}' | sort -k 1b,1 | join - %s |"
               "awk '$4 != $3 {print}' | wc -l | awk '{print $1}' ") % \
               (previous_file, available_file, ifile)
    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    count = perform.execute(
        command, pipe=True, langC=True
    ).read().split()[0]
    if os.path.exists(ifile):
        os.remove(ifile)
    return count


def reset_files():
    if os.path.exists(available_file):
        os.remove(available_file)
    if os.path.exists(previous_file):
        os.remove(previous_file)
    update_available(noreport=True)


def ensure_initialised():
    """Create the init_dir and files if they don't exist."""
    if not os.path.exists(available_file):
        reset_files()


def backup_before_upgrade(packages):
    """Backup packages before a (dist)upgrade.

     This optional functionality helps recovery in case of trouble caused
     by the newly-installed packages. The packages are by default stored
     in a directory named like  ~/.wajig/hostname/backups/2010-09-21_09h21."""

    date = time.strftime("%Y-%m-%d_%Hh%M", time.localtime())
    target = os.path.join(init_dir, "backups", date)
    if not os.path.exists(target):
        os.makedirs(target)
    os.chdir(target)
    print("The packages will saved in", target)
    for package in packages:
        command = "fakeroot -u dpkg-repack " + package
        perform.execute(command)


def requires_package(package, path=None):
    import shutil
    if not path:
        path = package
    if shutil.which(path):
        return True
    print(f"\nThis command depends on '{package}' which can be installed with:\n\n" +
          f"wajig install {package}\n")
    sys.exit(1)


def package_exists(cache, package, ignore_virtual_packages=False):
    try:
        if cache.is_virtual_package(package) and not ignore_virtual_packages:
            return cache.get_providing_packages(package)[0]
        return cache[package]
    except KeyError as error:
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
    """Retrieve Debian changelog from local installation."""
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
    if not package.candidate:
        return
    for dependency_list in package.candidate.get_dependencies(dependency_type):
        for dependency in dependency_list.or_dependencies:
            yield dependency.name


def do_describe(packages, verbose=False, die=True):
    """Display package description(s)"""

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
                import subprocess
                command = 'dpkg --print-foreign-architectures'.split()
                output = subprocess.check_output(command)
                for arch in output.decode().split():
                    try:
                        package = cache["{}:{}".format(package, arch)]
                        # to avoid noise, only consider the 1st match
                        break
                    except KeyError:
                        pass
                if not isinstance(package, apt.package.Package) and die:
                    print(str(e).strip('"'))
                    return 1
            packageversion = package.installed
            if not packageversion:  # if package is not installed...
                packageversion = package.candidate
            packageversions.append((
                package.shortname, packageversion.summary,
                packageversion.description
            ))
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


def show_package_versions():
    packages = upgradable(get_names_only=False)
    if packages:
        print("{:<24} {:<24} {}".format("Package", "Available", "Installed"))
        print("="*24 + "-" + "="*24 + "-" + "="*24)
        for package in sorted(packages):
            message = "{:<24} {:<24} {}".format(
                package.name,
                package.candidate.version,
                package.installed.version,
            )
            print(message)
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
    """List status of the packages identified"""

    if not snapshot:
        print("%-23s %-15s %-15s %-15s %s" % \
              ("Package", "Installed", "Previous", "Now", "State"))
        print("="*23 + "-" + "="*15 + "-" + "="*15 + "-" + "="*15 + "-" + "="*5)
        sys.stdout.flush()

    # Generate a temporary file of installed packages.
    ifile = tempfile.mkstemp()[1]

    perform.execute(gen_installed_command_str() + " > " + ifile,
                    langC=True)
    # Build the command to list the status of installed packages.
    command = "dpkg --get-selections | sort | join - " + ifile + " | " +\
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

    # Check whether the package is not in the installed list, and if not
    # list its status appropriately.
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


def do_listnames(pattern=False, pipe=False, teach=False, noop=False):

    # If user can't access /etc/apt/sources.list then must do this with
    # sudo or else most packages will not be found.
    needsudo = not os.access("/etc/apt/sources.list", os.R_OK)
    if pattern:
        command = "apt-cache pkgnames | grep -E -- " + pattern \
                + " | sort -k 1b,1"
    else:
        command = "apt-cache pkgnames | sort -k 1b,1"
    # Start fix for Bug #292581 - pre-run command to check for no output
    results = perform.execute(command, root=needsudo, pipe=True,
                              teach=teach, noop=noop)
    if results:
        lines = results.readlines()
        if lines:
            return perform.execute(command, root=needsudo, pipe=pipe)
    else:
        sys.exit(1)


def do_update(simulate=False):
    if not perform.execute("apt update", root=True):
        if not simulate:
            update_available()
            print("There are {} new upgrades".format(count_upgrades()))


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
        package_name = section.get("Package")
        package_size = section.get("Installed-Size")
        package_status = re.split(" ", section.get("Status"))[2]
        if package_size and float(package_size) > size:
            if package_name not in size_list:
                size_list[package_name] = package_size
                status_list[package_name] = package_status

    packages = list(size_list)
    packages.sort(key=lambda x: int(size_list[x]))  # sort by size

    if packages:
        print("{:<33} {:^10} {:>12}".format("Package", "Size (KB)", "Status"))
        print("{}-{}-{}".format("="*33, "="*10, "="*12))
        for package in packages:
            message = "{:<33} {:^10} {:>12}".format(
                package,
                format(int(size_list[package]), ',d'),
                status_list[package],
            )
            print(message)
    else:
        print("No packages of >10MB size found")


log_file = os.path.join(init_dir, 'Log')

def start_log(old_log):
    "Write a list of installed packages to a tmp file."
    perform.execute(gen_installed_command_str() + " > " + old_log,
                    langC=True)


def finish_log(old_log):
    ts = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S')
    # Generate new list of installed and compare to old
    lf = open(log_file, "a")
    new_iter = perform.execute(gen_installed_command_str(),
                               langC=True, pipe=True)
    old_iter = open(old_log)
    for o in old_iter:
        o = o.strip().split(" ")
        n = new_iter.__next__().strip().split(" ")
        while o[0] != n[0]:
            if o[0] < n[0]:
                lf.write("{0} {1} {2} {3}\n".format(ts, "remove", o[0], o[1]))
                o = old_iter.__next__().strip().split(" ")
            elif o[0] > n[0]:
                lf.write("{0} {1} {2} {3}\n".format(ts, "install", n[0], n[1]))
                n = new_iter.__next__().strip().split(" ")

        if o[1] != n[1]:
            old_version = o[1].split(".")  # for a more accurate comparison
            new_version = n[1].split(".")  # same
            if old_version > new_version:
                lf.write(
                    "{0} {1} {2} {3}\n".format(ts, "downgrade", n[0], n[1])
                )
            else:
                lf.write("{0} {1} {2} {3}\n".format(ts, "upgrade", n[0], n[1]))

    os.remove(old_log)
