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
import subprocess


SIMULATE = False
TEACH = False

output = subprocess.check_output("dpkg --get-selections".split())
output = output.decode().split()
if "sudo" in output and not os.getuid():
    setroot = "/usr/bin/sudo"
    # In case someone is using the non-default install of sudo on
    # Debian (the default install uses a default root path for sudo
    # which includes sbin) or have added this user to the sudo group
    # (which has the effect of also using the user's path rather than
    # the root path), add the sbin directories to the PATH.
    os.environ['PATH'] = os.environ['PATH'] + ":/sbin:/usr/sbin"
else:
    setroot = "/bin/su"


def execute(command, root=False, pipe=False, langC=False, test=False,
            getoutput=False):
    """Ask the operating system to perform a command.

    Arguments:

    COMMAND     A string containing the command and command line options
    ROOT        If True, root access is required to execute command
    PIPE        If True then return a file-like object.
    LANGC       If LC_TYPE=C is needed (as in join in status command)

    Returns either the status of the command or a file-like object
    if PIPE is True."""

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
            if '|' in command and subprocess.call(setroot + " -v", shell=True):
                raise SystemExit("sudo authentication failed.")
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
        else:
            if os.getuid() and not test:
                print("Using `su' and requiring root password. Install `sudo' "
                      "to support user passwords. See wajig documentation "
                      "(wajig doc) for details.")
                command = "{} -c '{}'".format(setroot, command)

    # This worked a long time until Bug#288852 from Serge Matveev
    # <serge@matveev.spb.ru> reported that locale is not handled -
    # which is correct and according to the fix of Bug#119899 the
    # language was specifially put to be C to make the join work in
    # the status command. So the fix now is to not touch the locale
    # except if the cammand asks for it through the langC flag.
    #
    if langC:
        command = "LC_ALL=C; export LC_ALL; " + command
    if test:
        return command
    elif SIMULATE:
        print(command)
        return
    if TEACH:
        print("EXECUTING: " + command)
    if pipe:
        return os.popen(command)
    elif getoutput:
        return subprocess.check_output(command, shell=True,
                                       stderr=subprocess.STDOUT)
    else:
        return subprocess.call(command, shell=True)
