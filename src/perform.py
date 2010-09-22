# WAJIG - Debian Package Management Front End
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

#------------------------------------------------------------------------
#
# Standard python modules
#
#------------------------------------------------------------------------
import os
import getpass

setroot = "/bin/su"
#
# TODO - ONLY SET TO sudo IF USER IS IN THE sudoers FILE. THUS THE
# FALL BACK IS TO USING su EVEN IF sudo IS INSTALLED.
#
user = ""

try:
    user = os.environ['USER']
except:
    pass

try:
    if not user:
        user = getpass.getuser()
except:
    user = 'unknown'

if os.path.exists("/usr/bin/sudo") and user != 'root':
    setroot = "/usr/bin/sudo"
    #
    # In case someone is using the non-default install of sudo on
    # Debian (the default install uses a default root path for sudo
    # which includes sbin) or have added this user to the sudo group
    # (which has the effect of also using the user's path rather than
    # the root path), add the sbin directories to the PATH.
    #
    os.environ['PATH'] = os.environ['PATH'] + ":/sbin:/usr/sbin"

#------------------------------------------------------------------------
#
# Interface Variables
#
#------------------------------------------------------------------------

quiet = ""
simulate = False
teaching = False

def set_quiet(check=True):
    global quiet
    if check:
        quiet = "> /dev/null"
    else:
        quiet = ""


def set_teaching():
    global teaching
    teaching = True


def set_simulate(new_level):
    global simulate
    simulate = new_level


def execute(command, root=False, noquiet=False, display=True, pipe=False,
            langC=False, test=False):
    """Ask the operating system to perform a command.

    Arguments:

    COMMAND     A string containing the command and command line options
    ROOT        If non-zero then root access is required to execute command
    NOQUIET     Suppress the use of quiet (in case command has a redirect)
    PIPE        If True then return a file-like object.
    LANGC       If LC_TYPE=C is needed (as in join in status command)

    Returns:

    Returns either the status of the command or a file-like object
    if PIPE is True.

    Note that the PIPE option was added as a minor modification and has not
    been fully tested, but is extremely useful in avoiding temporary files."""

    if teaching:
        if test:
            return "Performing: " + command
        print "Performing: " + command
    elif simulate and display:
        if test:
            return command
        print command
    if root:
        if setroot == "/usr/bin/sudo":
            #
            # Bug #320126. Karl suggested that we use -v to preset the
            # password, which also avoids mixing password failure
            # with command failure but this causes password to be
            # asked for even if the sudoers file indicates a password
            # is not required. But this happens in only a few cases,
            # like listnames (in user has no access to sources.list),
            # hold, unhold. So should be sufferable.
            #
            if '|' in command and os.system(setroot + " -v"):
                raise SystemExit("wajig: sudo authentication failed.")
            #
            # Bug #320126 noted the following is not good as is since
            # the password is asked for multiple times in a pipe
            # before it is cached.  It captures the case where the
            # command contains a pipe, and requires root. Then each
            # part is done as sudo.  TODO: It's not always true that
            # root is required for each part!  E.g. HOLD doesn't need
            # it: echo package hold | dpkg --set-selections
            #
            command = setroot + " " + command.replace("|", "| %s " % setroot)
            #
            # Did try packaging the sudo up in a sh command. But then
            # this loses the tuning of sudoers to just the APT commands.
            # and also required /bin/sh to be NOPASSWD'ed if wanted
            # password-less wajig.
            #
            # command = setroot + " sh -c '%s'" % command
            #
            # Decide to always require a password, even if sudoers
            # says NOPASSWD. Only other alternative might be to store
            # intermediate results in temporary files.
        else:
            if quiet == "" and user != "root" and not test:
                print """
Using `su' and requiring root password. Install `sudo' to support user
passwords. See wajig documentation (wajig doc) for details.
"""
            command = setroot + " -c '" + command + "'"
    if not noquiet:
        command = command + quiet
    #
    # Bug#119899 from Michal Politowski <mpol@charybda.icm.edu.pl>
    # was implemented to ensure handling Polish language okay:
    #
    # command = "LC_ALL=C; export LC_ALL; set -o noglob; " + command
    command = "set -o noglob; " + command
    #
    # This worked a long time until Bug#288852 from Serge Matveev
    # <serge@matveev.spb.ru> reported that locale is not handled -
    # which is correct and according to the fix of Bug#119899 the
    # language was specifially put to be C to make the join work in
    # the status command. So the fix now is to not touch the locale
    # except if the cammand asks for it through the langC flag.
    #
    if langC:
        command = "LC_ALL=C; export LC_ALL; " + command
    if not simulate and not test:
        if pipe:
            return os.popen(command)
        else:
            return os.system(command)
    if test:
        return command
    return 0
