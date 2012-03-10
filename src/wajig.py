#!/usr/bin/env python3
#
# WAJIG - Debian Command Line System Administrator
#
# Copyright (c) Graham.Williams@togaware.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version. See the file LICENSE.
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

# stdlib
import sys
import re
import argparse
import textwrap

# wajig modules
import commands
import changes
import util
import const

yes = str()
noauth = str()


def main():
    global yes
    global noauth

    # remove commas and insert the arguments appropriately
    oldargv = sys.argv
    sys.argv = oldargv[0:2]
    for i in range(2, len(oldargv)):
        sys.argv += oldargv[i].split(",")

    description = ("wajig is a simple and unified package management "
                   "front-end for Debian and its derivatives.")
    epilog = textwrap.dedent("""\
         For a list of all commands try "wajig list-commands".
         For a tutorial, try "wajig doc".
         Full documentation is at http://www.togaware.com/wajig.""")
    usage = "%(prog)s [options] COMMAND [arguments]"
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                     formatter_class=argparse.RawDescriptionHelpFormatter,
                     prog="wajig", usage=usage)

    message = ("backup packages currently installed packages before replacing "
               "them; used in conjuntion with [DIST]UPGRADE commands")
    parser.add_argument("-b", "--backup", action='store_true', help=message)

    message = ("turn on verbose output")
    parser.add_argument("-v", "--verbose", action="store_true", help=message)

    message = ("uses the faster apt-cache instead of the slower (but more "
               "advanced) aptitude to display package info; used in "
               "conjunction with SHOW command")
    parser.add_argument("-f", "--fast", action='store_true', help=message)

    message = ("install with Recommended dependencies; used in "
               "conjunction with INSTALL command")
    parser.add_argument("-r", "--recommends", action='store_true',
                        default=True, help=message)

    message = ("do not install with Recommended dependencies; used in "
               "conjunction with INSTALL command")
    parser.add_argument("-R", "--norecommends", action='store_false',
                        help=message)

    message = "a dangerous option that skips 'Yes/No' prompts'"
    parser.add_argument("-y", "--yes", action='store_true', help=message)

    message = "do not authenticate packages before installation"
    parser.add_argument("-n", "--noauth", action='store_true', help=message)

    message = ("specify a distribution to use (e.g. testing or experimental)")
    parser.add_argument("-d", "--dist", help=message)

    message = "show wajig version"
    parser.add_argument("-V", "--version", action="version", help=message,
                        version=const.version)

    parser.add_argument("args", nargs="*")

    result = parser.parse_args()
    util.fast = result.fast
    util.recommends_flag = result.recommends
    util.recommends_flag = result.norecommends
    args = result.args
    if not result.dist:
        result.dist = ""
    if result.yes:
        yes = " --yes "
    if result.noauth:
        noauth = " --allow-unauthenticated "

    #
    # Process the command. Lowercase it so that we allow any case
    # for commands and allow hyphens and underscores and slash.
    #
    # Need to check for install/sarge-backport and not convert the
    # part after the / (Bug##350944)
    #
    if not args:
        print("You must specify an argument; Run 'wajig commands' for a list")
        util.finishup(1)
    slash = args[0].find("/")
    if slash == -1:
        command = re.sub('-|_|/', '', args[0].lower())
    else:
        command = re.sub('-|_|/', '', args[0][:slash].lower()) +\
                  args[0][slash + 1:]

    # 081222 remove any commas - this makes it easier to copy and
    # paste from the security status email, for example.

    args = [x for x in args if x != ""]

    # Before we do any other command make sure the right files exist.
    changes.ensure_initialised()
    select_command(command, args, result.verbose, result.dist, result.backup)


def select_command(command, args, verbose, dist, backup):
    "Select the appropriate command and execute it."

    global yes

    if command in ["addcdrom", "cdromadd"]:
        commands.addcdrom(args)

    elif command == "addrepo":
        commands.addrepo(args)

    elif command in ["autoalts", "autoalternatives"]:
        commands.autoalts(args)

    elif command == "autodownload":
        commands.autodownload(args, verbose)

    elif command == "autoclean":
        commands.autoclean(args)

    elif command == "autoremove":
        commands.autoremove(args)

    elif command in "reportbug bug bugreport".split():
        commands.reportbug(args)

    elif command == "build":
        commands.build(args, yes, noauth)

    elif command in "builddepend builddepends builddep builddeps".split():
        commands.builddeps(args, yes, noauth)

    elif command in "reversebuilddepends rbuilddeps rbuilddep".split():
        commands.rbuilddeps(args)

    elif command == "changelog":
        commands.changelog(args, verbose)

    elif command == "clean":
        commands.clean(args)

    elif command == "contents":
        commands.contents(args)

    elif command == "dailyupgrade":
        commands.dailyupgrade(args)

    elif command == "dependents":
        commands.dependents(args)

    elif command in ["describe", "whatis"]:
        commands.describe(args, verbose)

    elif command in ["describenew", "newdescribe"]:
        commands.describenew(args, verbose)

    elif command in ["detail", "details", "show"]:
        commands.show(args)

    elif command in ["detailnew", "newdetail"]:
        commands.newdetail(args)

    elif command == "upgrade":
        commands.upgrade(args, yes, noauth, backup)

    elif command == "distupgrade":
        commands.distupgrade(args, yes, noauth, backup)

    elif command in "doc docs documentation tutorial".split():
        commands.tutorial(args)

    elif command == "download":
        commands.download(args)

    elif command == "editsources":
        commands.editsources(args)

    elif command == "extract":
        commands.extract(args)

    elif command in "findfile locate filesearch whichpkg whichpackage".split():
        commands.whichpackage(args)

    elif command in "findpkg findpackage unofficial".split():
        commands.unofficial(args)

    elif command == "fixconfigure":
        commands.fixconfigure(args)

    elif command == "fixinstall":
        commands.fixinstall(args, noauth)

    elif command == "fixmissing":
        commands.fixmissing(args, noauth)

    elif command == "force":
        commands.force(args, noauth)

    elif command == "help":
        commands.help(args)

    elif command == "hold":
        commands.hold(args)

    elif command == "info":
        commands.hold(args)

    elif command in ["init", "reset"]:
        commands.init(args)

    elif command in "install isntall autoinstall".split():
        commands.install(args, yes, noauth, dist)

    elif command in "installs suggested installsuggested".split():
        commands.installsuggested(args, yes, noauth, dist)

    elif args[0].startswith('install') and "/" in args[0]:
        commands.installwithdist(args, yes, noauth, dist)

    elif command == "integrity":
        commands.integrity(args)

    elif command == "large":
        commands.large(args)

    elif command == "lastupdate":
        commands.lastupdate(args)

    elif command == "list":
        commands.listpackages(args)

    elif command in ["listalts", "listalternatives"]:
        commands.listalternatives(args)

    elif command == "listcache":
        commands.listcache(args)

    elif command in ["listcommands", "commands"]:
        commands.listcommands(args)

    elif command == "listdaemons":
        commands.listdaemons(args)

    elif command == "listfiles":
        commands.listfiles(args)

    elif command == "listsection":
        commands.listsection(args)

    elif command == "listsections":
        commands.listsections(args)

    elif command == "listhold":
        commands.listhold(args)

    elif command == "listinstalled":
        commands.listinstalled(args)

    elif command in "listlog syslog".split():
        commands.syslog(args)

    elif command == "listnames":
        commands.listnames(args)

    elif command == "listscripts":
        commands.listscripts(args)

    elif command == "liststatus":
        commands.liststatus(args)

    elif command == "localdistupgrade":
        commands.localdistupgrade(args)

    elif command == "localupgrade":
        commands.localupgrade(args)

    elif command == "madison":
        commands.madison(args)

    elif command == "move":
        commands.move(args)

    elif command == "new":
        commands.new(args)

    elif command in ["newupgrades", "newupgrade"]:
        commands.newupgrades(args, yes, noauth)

    elif command == "nonfree":
        commands.nonfree(args)

    elif command in "orphans orphaned listorphaned listorphans".split():
        commands.orphans(args)

    elif command in ["policy", "available"]:
        commands.policy(args)

    elif command in ["purge", "purgedepend"]:
        commands.purge(args, yes, noauth)

    elif command == "purgeorphans":
        commands.purgeorphans(args)

    elif command == "purgeremoved":
        commands.purgeremoved(args)

    elif command == "readme":
        commands.readme(command, args)

    elif command == "news":
        commands.news(args)

    elif command == "recommended":
        commands.recommended(args)

    elif command in "recursive recdownload".split():
        commands.recdownload(args)

    elif command == "reconfigure":
        commands.reconfigure(args)

    elif command == "reinstall":
        commands.reinstall(args, noauth, yes)

    elif command == "reload":
        commands.reload(args)

    elif command == "restart":
        commands.restart(args)

    elif command == "start":
        commands.start(args)

    elif command == "stop":
        commands.stop(args)

    elif command in ["remove", "removedepend"]:
        commands.remove(args, noauth, yes)

    elif command == "removeorphans":
        commands.removeorphans(args)

    elif command in ["repackage", "package"]:
        commands.repackage(args)

    elif command == "rpminstall":
        commands.rpminstall(args)

    elif command in ["rpmtodeb", "rpm2deb"]:
        commands.rpm2deb(args)

    elif command == "search":
        commands.search(args, verbose)

    elif command == "searchapt":
        commands.searchapt(args)

    elif command == "showdistupgrade":
        commands.showdistupgrade(args)

    elif command == "showinstall":
        commands.showinstall(args)

    elif command == "showremove":
        commands.showremove(args)

    elif command == "showupgrade":
        commands.showupgrade(args)

    elif command in ["size", "sizes"]:
        commands.sizes(args)

    elif command == "snapshot":
        commands.snapshot(args)

    elif command == "source":
        commands.source(args)

    elif command == "status":
        commands.status(args)

    elif command in ["statusmatch", "statussearch"]:
        commands.statusmatch(args)

    elif command == "tasksel":
        commands.tasksel(args)

    elif command == "toupgrade":
        commands.toupgrade(args)

    elif command == "unhold":
        commands.unhold(args)

    elif command == "update":
        commands.update(args)

    # For testing only!
    elif command == "updateavailable":
        commands.updateavailable(args)

    elif command in ["updatealts", "updatealternatives",
                     "setalts", "setalternatives"]:
        commands.updatealternatives(args)

    elif command == "updatepciids":
        commands.updatepciids(args)

    elif command == "updateusbids":
        commands.updateusbids(args)

    elif command == "upgradesecurity":
        commands.upgradesecurity(args)

    elif command == "verify":
        commands.verify(args)

    elif command == "versions":
        commands.versions(args)

    else:
        print("Command not recognised; run 'wajig commands' for a list")


if __name__ == '__main__':
    main()
