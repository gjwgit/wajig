#
# WAJIG - Debian Package Management Front End
#
# Keep track of changes between UPDATEs
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

#
# TODO: Perhaps better to call this "package" rather than "changes".

import os
import tempfile
import socket
import datetime
import time

import apt
import apt_pkg

import perform

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
available_file = init_dir + "/Available"
previous_file  = init_dir + "/Available.prv"

# removes a no-longer-used log file
# this code should go away after Debian 7.0 is released
log_file = init_dir + "/Log"
if os.path.exists(log_file):
    os.remove(log_file)

# Set the temporary directory to the init_dir.
# Large files are not generally written there so should be okay.
tempfile.tempdir = init_dir


def update_available(noreport=False):
    """Generate current list of available packages, backing up the old list.

    noreport    If set, do not report on the number of packages.
    """

    if not os.path.exists(available_file):
        f = open(available_file, "w")
        f.close()

    temporary_file = tempfile.mkstemp()[1]

    os.rename(available_file, temporary_file)
    command = "apt-cache dumpavail " +\
              "| egrep '^(Package|Version):' " +\
              "| tr '\n' ' '" +\
              "| perl -p -e 's|Package: |\n|g; s|Version: ||g'" +\
              "| sort -k 1b,1 | tail -n +2 | sed 's| $||' > " + available_file
    # Use langC in the following since it uses a grep.
    perform.execute(command, langC=True)  # root is not required.
    os.rename(temporary_file, previous_file)

    available_packages = len(open(available_file).readlines())
    previous_packages = len(open(previous_file).readlines())
    diff = available_packages - previous_packages

    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    command = "join -v 1 -t' '  {0} {1} | wc -l"
    command = command.format(available_file, previous_file)
    newest = perform.execute(command, pipe=True, langC=True)
    newest = newest.readlines()[0].strip()

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
    "Generate command to list installed packages and their status."
    command = "cat /var/lib/dpkg/status | " +\
              "egrep '^(Package|Status|Version):' | " +\
              "awk '/^Package: / {pkg=$2} " +\
              "     /^Status: / {s1=$2;s2=$3;s3=$4}" +\
              "     /^Version: / {print pkg,$2,s1,s2,s3}' | " +\
              "grep 'ok installed' | awk '{print $1,$2}' | sort -k 1b,1"
    return command


def count_upgrades():
    "Return as a string the number of new upgrades since last update."
    ifile = tempfile.mkstemp()[1]
    # Use langC in the following since it uses a grep.
    perform.execute(gen_installed_command_str() + " > " + ifile, langC=True)
    command = "join " + previous_file + " " + available_file + " |" +\
              "awk '$2 != $3 {print}' | sort -k 1b,1 | join - " + ifile + " |" +\
              "awk '$4 != $3 {print}' | wc -l | awk '{print $1}' "
    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    count = perform.execute(command, pipe=True,
            langC=True).read().split()[0]
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
    "Create the init_dir and files if they don't exist."
    if not os.path.exists(available_file):
        reset_files()


available_list = {}
previous_list = {}
installed_list = {}


def load_dictionaries():
    "Create dictionaries of avail/installed packages for in-memory tasks."

    ensure_initialised()

    afile = open(available_file, "r").readlines()
    for i in range(0, len(afile)):
        available_list[afile[i].split()[0]] = afile[i].split()[1]

    pfile = open(previous_file, "r").readlines()
    for i in range(0, len(pfile)):
        previous_list[pfile[i].split()[0]] = pfile[i].split()[1]

    ifile = perform.execute(gen_installed_command_str(), pipe=True).readlines()
    for i in range(0, len(ifile)):
        installed_list[ifile[i].split()[0]] = ifile[i].split()[1]


def get_available_list():
    "Obtain the dictionary of available packages."
    return available_list


def get_previous_list():
    "Obtain the dictionary of previously available packages."
    return previous_list


def get_previous_version(package):
    "Obtain the package's previously available version number."
    return previous_list[package]


def get_installed_version(package):
    "Return, as string, the package's installed version number."
    # TODO: Make sure the dictionary has been loaded.
    return installed_list[package]


def get_new_available():
    "Obtain the packages available now but not previously."
    load_dictionaries()
    new_list = []
    for package in available_list.keys():
        if not package in previous_list:
            new_list.append(package)
    return new_list


def get_new_upgrades():
    "Obtain newly-upgraded packages."
    load_dictionaries()
    upgraded_list = []
    apt_pkg.init_system()  # Not sure why!
    for package in installed_list.keys():
        if package in available_list and package in previous_list \
        and apt_pkg.version_compare(available_list[package],
        previous_list[package]) > 0:
            upgraded_list.append(package)
    return upgraded_list


def get_status(package):
    p = perform.execute("dpkg --status " + package, pipe=True)
    packageinfo = apt_pkg.TagFile(p)
    return packageinfo.next().get("Status")


def get_dependees(package):
    "Return a list of other installed pkgs that depend on PKG."
    packageinfo = perform.execute("apt-cache rdepends --installed " +
                               package, pipe=True)
    dp = []
    # Watch for changes to apt-cache output.
    if packageinfo.next().strip() != package:
        print("unexpected result from apt-cache - submit a bug report")
    if packageinfo.next().strip() != "Reverse Depends:":
        print("unexpected result from apt-cache - submit a bug report")
    for l in packageinfo:
        pn = l.strip().split(',')[0].replace('|', '')
        dp.append(pn)
    #
    # If dp is too long, don't check install status.
    # Just assume installed.
    # libc6 (over 7000), for exapmle, takes far too long.
    # Really just need to find first package that is installed
    # that depends on this package to rule it out.
    #
    np = []
    if len(dp) < 20:
        for p in dp:
            if get_status(p).find("not-installed") < 0:
                np.append(p)
    return np


def get_dependencies(package):
    "Return a list of installed packages that PKG depends on."
    packageinfo = perform.execute("apt-cache depends --installed " +
                              package, pipe=True)
    dp = []
    # Watch for changes to apt-cache output.
    if packageinfo.next().strip() != package:
        print("unexpected result from apt-cache - submit a bug report")
    # Find package names. Ignore "<name>" as these are not installed.
    for l in packageinfo:
        if l.find(":") >= 0 and l.find("<") < 0:
            dp.append(l.split()[1])
    return dp


def backup_before_upgrade(packages, distupgrade=False):
    """Backup packages before a (dist)upgrade.

     This optional functionality helps recovery in case of trouble caused
     by the newly-installed packages. The packages are by default stored
     in a directory named like  ~/.wajig/hostname/backups/2010-09-21_09h21."""

    date = time.strftime("%Y-%m-%d_%Hh%M", time.localtime())
    target = init_dir + "/backups/" + date
    if not os.path.exists(target):
        os.makedirs(target)
    os.chdir(target)
    print("The packages will saved in", target)
    for package in packages:
        command = "fakeroot -u dpkg-repack " + package
        perform.execute(command)
