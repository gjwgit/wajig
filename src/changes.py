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
# TODO
#
# Perhaps better to call this "package" rather than "changes"

#------------------------------------------------------------------------
#
# Standard python modules
#
#------------------------------------------------------------------------
import os
import tempfile
import socket
import datetime

#------------------------------------------------------------------------
#
# APT module
#
#------------------------------------------------------------------------
import apt_pkg

#------------------------------------------------------------------------
#
# Wajig modules
#
#------------------------------------------------------------------------
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

os.system("rm -f " + init_dir + "/tmp*")

#
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
#
available_file = init_dir + "/Available"
previous_file  = init_dir + "/Available.prv"
log_file       = init_dir + "/Log"
#
# No longer using the Installed file so remove it. 23 Aug 2003
#
if os.path.exists(init_dir + "/Installed"):
    os.remove(init_dir + "/Installed")
#
# Packages cache
#
# This was added when some /var/lib/dpkg/available stopped being
# updated for some reason - perhaps new version of dpkg or apt
# (Jun/Jul 03). File can be big, but hope that's okay.
#
# BUT no it is not okay! For large installations, this creates
# additional 11MB per host per user of wajig :-(
# Generateion of the file is quick (0.5s) so just build it
# as needed in /tmp. 23 Aug 2003
#
#packages_file  = init_dir + "/Packages"
#
# Remove the large cache file - this should only be needed
# for a little while as 0.3.26 replaced 0.3.25 pretty quickly.
# 23 Aug 2003
#
if os.path.exists(init_dir + "/Packages"):
    os.remove(init_dir + "/Packages")

#
# Set the temporary directory to the init_dir.
# Large files are not generally written there so should be okay.
#
tempfile.tempdir = init_dir


def get_available_filename():
    """Obtain the name of the file containing list of available packages.

    Arguments:

    Returns:
    string      The filename"""

    return available_file


def get_previous_filename():
    """Obtain the name of the file containing list of previous packages.

    Arguments:

    Returns:
    string      The filename"""

    return previous_file

#------------------------------------------------------------------------
#
# UPDATE AVAILABLE
#
#------------------------------------------------------------------------
def update_available(noreport=False):
    """Generate current list of available packages, backing up the old list.

    Arguments:
    noreport    If set then do not report on the number of packages.

    Returns:"""

    if not os.path.exists(available_file):
        f = open(available_file, "w")
        f.close()

    temporary_file = tempfile.mktemp()

    os.rename(available_file, temporary_file)
    command = "apt-cache dumpavail " +\
              "| egrep '^(Package|Version):' " +\
              "| tr '\n' ' '" +\
              "| perl -p -e 's|Package: |\n|g; s|Version: ||g'" +\
              "| sort -k 1b,1 | tail -n +2 | sed 's| $||' > " + available_file
    # Use langC in the following since it uses a grep.
    perform.execute(command, noquiet=True, langC=True)  # root is not required.
    os.rename(temporary_file, previous_file)

    available_packages = len(open(available_file).readlines())
    previous_packages = len(open(previous_file).readlines())
    diff = available_packages - previous_packages
    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    newest = perform.execute("join -v 1 -t' '  " +
                             available_file + " " +
                             previous_file +
                             " | wc -l", pipe=True, langC=True).readlines()[0].strip()
    if not noreport:
        if diff < 0:
            direction = str(0 - diff) + " down on"
        elif diff == 0:
            direction = "the same as"
        else:
            direction = str(diff) + " up on"
        #print "There are " + str(available_packages) + " packages now " +
        #      "available which is " + direction + " the previous count."
        print "This is " + direction + " the previous count",
        print "with " + newest + " new",
        if newest == "1":
            print "package."
        else:
            print "packages."

########################################################################
#
# UPDATE LOG
#
# Call start_log before any actions, then finish_log when actions are
# finished. This will write a summary of changes to the log file.
#
old_log = tempfile.mktemp()

def start_log():
    # Write list of installed to tmp file
    perform.execute(gen_installed_command_str() + " > " + old_log,
                    noquiet=1, langC=True)


def finish_log():
    ts = datetime.datetime.today().isoformat()
    ts = ts[:-10]  # Don't put seconds - it implies too much accuracy
    # Generate new list of installed and compare to old
    lf = file(log_file, "a")
    new_iter = perform.execute(gen_installed_command_str(),
                               noquiet=1, langC=True, pipe=True)
    old_iter = file(old_log)
    for o in old_iter:
        o = o.strip().split(" ")
        n = new_iter.next().strip().split(" ")
        while o[0] != n[0]:
            if o[0] < n[0]:
                lf.write("%s %s %s %s\n" % (ts, "remove", o[0], o[1]))
                o = old_iter.next().strip().split(" ")
            elif o[0] > n[0]:
                lf.write("%s %s %s %s\n" % (ts, "install", n[0], n[1]))
                n = new_iter.next().strip().split(" ")
        if o[1] != n[1]:
            lf.write("%s %s %s %s\n" % (ts, "upgrade", n[0], n[1]))
    os.remove(old_log)

#------------------------------------------------------------------------
#
# GET INSTALLED COMMAND STR
#
#------------------------------------------------------------------------
def gen_installed_command_str():
    """Generate command to list installed packages and their status."""
    command = "cat /var/lib/dpkg/status | " +\
              "egrep '^(Package|Status|Version):' | " +\
              "awk '/^Package: / {pkg=$2} " +\
              "     /^Status: / {s1=$2;s2=$3;s3=$4}" +\
              "     /^Version: / {print pkg,$2,s1,s2,s3}' | " +\
              "grep 'ok installed' | awk '{print $1,$2}' | sort -k 1b,1"
    return(command)


def count_upgrades():
    """Return as a string the number of new upgrades since last update."""
    ifile = tempfile.mktemp()
    # Use langC in the following since it uses a grep.
    perform.execute(gen_installed_command_str() + " > " + ifile,
                    langC=True, noquiet=1)
    command = "join " + previous_file + " " + available_file + " |" +\
              "awk '$2 != $3 {print}' | sort -k 1b,1 | join - " + ifile + " |" +\
              "awk '$4 != $3 {print}' | wc -l | awk '{print $1}' "
    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    count = perform.execute(command, noquiet=1, pipe=1,
            langC=True).read().split()[0]
    if os.path.exists(ifile):
        os.remove(ifile)
    return count


def reset_files():
    if os.path.exists(available_file):
        os.remove(available_file)
    if os.path.exists(previous_file):
        os.remove(previous_file)
    update_available(noreport=1)
    update_available(noreport=1)

#------------------------------------------------------------------------
#
# ENSURE INITIALISED
#
#------------------------------------------------------------------------
def ensure_initialised():
    """Make sure the init_dir and files exist and if not, create them.

    Arguments:

    Returns:"""

    if not os.path.exists(available_file):
        reset_files()

#------------------------------------------------------------------------
#
# Dictionaries of available, installed, and previously available packages.
#
#------------------------------------------------------------------------
available_list = {}
previous_list = {}
installed_list = {}


def load_dictionaries():
    """Create dictionaries of avail/installed packages for in-memory tasks."""

    ensure_initialised()

    afile = open(available_file, "r").readlines()
    for i in range(0, len(afile)):
        available_list[afile[i].split()[0]] = afile[i].split()[1]

    pfile = open(previous_file, "r").readlines()
    for i in range(0, len(pfile)):
        previous_list[pfile[i].split()[0]] = pfile[i].split()[1]

    ifile = perform.execute(gen_installed_command_str(),
                            noquiet=1, pipe=1).readlines()
    for i in range(0, len(ifile)):
        installed_list[ifile[i].split()[0]] = ifile[i].split()[1]


def get_available_list():
    """Obtain the dictionary of available packages.

    Arguments:

    Returns:
    dictionary  Available packages"""

    return available_list


def get_previous_list():
    """Obtain the dictionary of previously available packages.

    Arguments:

    Returns:
    dictionary  Previously available packages"""

    return previous_list


def get_available_version(pkg):
    """Obtain the package's available version number.

    Arguments:

    Returns:
    string      available version"""

    return available_list[pkg]


def get_previous_version(pkg):
    """Obtain the package's previously available version number.

    Arguments:

    Returns:
    string      Previous version"""

    return previous_list[pkg]


def get_installed_version(pkg):
    """Return, as string, the package's installed version number."""
    # TODO: Make sure the dictionary has been loaded.
    return installed_list[pkg]


def get_new_available():
    """Obtain the packages available now but not previously.

    Arguments:

    Returns:
    list        New packages"""
    load_dictionaries()
    new_list = []
    for pkg in available_list.keys():
        if not pkg in previous_list:
            new_list.append(pkg)
    return new_list


def get_new_upgrades():
    """Obtain the packages upgraded since previously.

    Arguments:

    Returns:
    list        Newly upgraded packages"""
    load_dictionaries()
    upgraded_list = []
    apt_pkg.init_system()  # Not sure why!
    for pkg in installed_list.keys():
        if pkg in available_list and pkg in previous_list \
        and apt_pkg.version_compare(available_list[pkg],
        previous_list[pkg]) > 0:
            upgraded_list.append(pkg)
    return upgraded_list


def get_to_upgrade():
    """Obtain the packages with newer versions available.

    Arguments:

    Returns:
    list        Upgradeable packages"""

    load_dictionaries()
    upgraded_list = []
    apt_pkg.init_system()  # Not sure why!
    for pkg in installed_list.keys():
        if pkg in available_list \
        and apt_pkg.version_compare(available_list[pkg],
        installed_list[pkg]) > 0:
            upgraded_list.append(pkg)
    return upgraded_list


def get_status(pkg):
    p = perform.execute("dpkg --status " + pkg, pipe=True)
    pkginfo = apt_pkg.TagFile(p)
    return pkginfo.next().get("Status")


def get_dependees(pkg):
    """Return a list of other installed pkgs that depend on PKG."""
    pkginfo = perform.execute("apt-cache rdepends --installed " +
                              pkg, pipe=True)
    dp = []
    # Watch for changes to apt-cache output.
    if pkginfo.next().strip() != pkg:
        print "wajig: unexpected result from apt-cache - submit a bug report"
    if pkginfo.next().strip() != "Reverse Depends:":
        print "wajig: unexpected result from apt-cache - submit a bug report"
    for l in pkginfo:
        pn = l.strip().split(',')[0].replace('|', '')
        dp.append(pn)
    #
    # If dp is too long, don't check install status.
    # Just assume installed.
    # libc6 (over 7000), for exapmle, takes far too long.
    # Really just need to find first pkg that is installed
    # that depends on this pkg to rule it out.
    #
    np = []
    if len(dp) < 20:
        for p in dp:
            if get_status(p).find("not-installed") < 0:
                np.append(p)
    return np


def get_dependencies(pkg):
    """Return a list of installed packages that PKG depends on."""
    pkginfo = perform.execute("apt-cache depends --installed " +
                              pkg, pipe=True)
    dp = []
    # Watch for changes to apt-cache output.
    if pkginfo.next().strip() != pkg:
        print "wajig: unexpected result from apt-cache - submit a bug report"
    # Find package names. Ignore "<name>" as these are not installed.
    for l in pkginfo:
        if l.find(":") >= 0 and l.find("<") < 0:
            dp.append(l.split()[1])
    return dp
