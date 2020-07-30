# This file is part of wajig.  The copyright file is at debian/copyright.

import os
import subprocess

def highlight(text):
    return "\x1b[1m{}\x1b[0m".format(text)

output = subprocess.check_output("dpkg --get-selections".split())
output = output.decode().split()
if "sudo" in output and os.getuid():
    setroot = "/usr/bin/sudo"
    # In case someone is using the non-default install of sudo on
    # Debian (the default install uses a default root path for sudo
    # which includes sbin) or have added this user to the sudo group
    # (which has the effect of also using the user's path rather than
    # the root path), add the sbin directories to the PATH.
    os.environ['PATH'] = os.environ['PATH'] + ":/sbin:/usr/sbin"
else:
    setroot = "/bin/su"


def execute(command, root=False, pipe=False, langC=False,
            getoutput=False, log=False, teach=False, noop=False):
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
        elif os.getuid():
            print(
                "Using `su' and requiring root password. Install `sudo' "
                "to support user passwords. See wajig documentation "
                "(wajig doc) for details."
            )
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
    if noop:
        print(highlight(" ".join(command.split())))
        return
    if teach:
        print(highlight(" ".join(command.split())))
    if pipe:
        return os.popen(command)
    if getoutput:
        return subprocess.check_output(command, shell=True,
                                       stderr=subprocess.STDOUT)
    if log:
        import tempfile
        import wajig.util as util
        temp = tempfile.mkstemp(dir='/tmp', prefix='wajig_')[1]
        util.start_log(temp)
    result = subprocess.call(command, shell=True)
    if log:
        util.finish_log(temp)
    return result
