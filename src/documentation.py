#
# JIG - Debian Administration Manager
#
# Documentation for wajig
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

import const


def version():
    print("\nJIG " + const.version + \
    """ - Command-line system admin for Debian GNU/Linux

    Copyright (c) Graham.Williams@togaware.com

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    On Debian systems, it may be found in /usr/share/common-licenses/GPL.
    """)


def usage():
    print("""
Usage:
 wajig [options] [command] [packages|files] ...

 wajig is a simple and unified package management front-end for Debian.

 For a mini-tutorial try "wajig help".
 For a list of all commands try "wajig list-commands".
 A more complete turorial is available with "wajig doc".
 Full documentation is at http://www.togaware.com/wajig.

""")


def help(verbose):

    if verbose == 0:
        print("""
 A mini-tutorial:

 update         Update the list of downloadable packages

 new            List packages that became available since last update
 newupgrades    List packages newly available for upgrading

 install        Install (or upgrade) one or more packages or .deb files
 remove         Remove one or more packages (see also purge)

 toupgrade      List packages with newer versions available for upgrading
 upgrade        Upgrade all of the installed packages or just those listed

 listnames      List all known packages or those containing supplied string
 whatis         For each package named obtain a one line description
 whichpkg       Find the package that supplies the given command or file

Run 'wajig COMMANDS' for a complete list of commands.
""")

    # ALL COMMANDS AND OPTIONS
    elif verbose == 1:
        with open("/usr/share/wajig/help/COMMANDS") as f:
            print()
            for line in f:
                print(line, end=' ')
            print()
    # TUTORIAL
    else:
        with open("/usr/share/wajig/help/TUTORIAL") as f:
            for line in f:
                print(line, end=' ')
