#!/usr/bin/python3
#
# wajig - Debian Command Line System Administrator
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

import argparse
import sys

import wajig.util as util
import wajig.commands as commands

from wajig.constants import APP, VERSION

def main():

    # without arguments, run a wajig shell (interactive mode)
    if len(sys.argv) == 1:
        import subprocess
        command = "python3 /usr/share/wajig/shell.py"
        subprocess.call(command.split())
        return

    parser = argparse.ArgumentParser(
        prog=APP,
        # usage="wajig [-h] [-V] [<command>] [--help] [--teach] [--noop] [<options>]",
        description="Unified package management front-end for Debian/Ubuntu.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "'wajig commands' to display available commands.\n"
            "'wajig <command> --help' for command sepcific help.\n"
            "'wajig doc | most' to display a tutorial.\n\n"
            "See what's happening with --teach or --noop.\n\n"
            "Please direct queries to https://stackoverflow.com/ and tag as wajig."
        ),
    )

    parser_backup = argparse.ArgumentParser(add_help=False)
    message = "backup currently installed packages before replacing them"
    parser_backup.add_argument(
        "-b", "--backup", action='store_true', help=message
    )

    parser_teach = argparse.ArgumentParser(add_help=False)
    group = parser_teach.add_mutually_exclusive_group()
    group.add_argument(
        "-s", "--noop", action='store_true',
        help="simulate command execution but do not perform"
    )
    group.add_argument(
        "-t", "--teach", action='store_true',
        help="display commands to be executed, before actual execution"
    )

    parser_verbose = argparse.ArgumentParser(add_help=False)
    message = "turn on verbose output"
    parser_verbose.add_argument(
        "-v", "--verbose", action="store_true", help=message
    )

    parser_fast = argparse.ArgumentParser(add_help=False)
    message = (
        "uses the faster apt-cache instead of the slower (but more "
        "advanced) aptitude to display package info"
    )
    parser_fast.add_argument("-f", "--fast", action='store_true', help=message)

    parser_recommends = argparse.ArgumentParser(add_help=False)
    group = parser_recommends.add_mutually_exclusive_group()
    message = "install Recommend dependencies (Debian default)"
    group.add_argument("-r", "--recommends", action='store_true', help=message)
    message = "do not install Recommend dependencies"
    group.add_argument(
        "-R", "--norecommends", action='store_true', help=message
    )

    parser_yesno = argparse.ArgumentParser(add_help=False)
    message = "skip 'Yes/No' confirmation prompts; use with care!"
    parser_yesno.add_argument("-y", "--yes", action='store_true', help=message)

    parser_auth = argparse.ArgumentParser(add_help=False)
    parser_auth.add_argument(
        "-n", "--noauth", action='store_true',
        help="do not authenticate packages before installation",
    )

    parser_dist = argparse.ArgumentParser(add_help=False)
    message = "specify a distribution to use (e.g. testing or experimental)"
    parser_dist.add_argument("-d", "--dist", help=message)

    parser_fileinput = argparse.ArgumentParser(add_help=False)
    parser_fileinput.add_argument(
        "-f", "--fileinput", action="store_true",
        help=(
            "if any of the arguments are files, assume their contents to "
            "be packages names"
        )
    )

    parser_local = argparse.ArgumentParser(add_help=False)
    parser_local.add_argument(
        "-l", "--local", action="store_true",
        help="use packages from local cache; don't download anything",
    )

    parser_grep = argparse.ArgumentParser(add_help=False)
    parser_grep.add_argument(
        "pattern", nargs="?",
        help="filter output, somewhat like grep",
    )

    message = "show wajig version"
    parser.add_argument(
        "-V", "--version", action="version", help=message,
        version="%(prog)s " + VERSION
    )

    subparsers = parser.add_subparsers(
        title='subcommands', help=argparse.SUPPRESS
    )

    def help(args):
        args.parser.print_help()
    parser_help = subparsers.add_parser("help")
    parser_help.set_defaults(func=help, parser=parser)

    # ADDCDROM
    
    function = commands.addcdrom
    parser_addcdrom = subparsers.add_parser(
        "addcdrom",
        aliases=["add-cdrom"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_addcdrom.set_defaults(func=function)

    # ADDREPO
    
    function = commands.addrepo
    parser_addrepo = subparsers.add_parser(
        "addrepo",
        parents=[parser_yesno, parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_addrepo.add_argument("ppa")
    parser_addrepo.set_defaults(func=function)

    # ADDUSER
    
    function = commands.adduser
    parser_adduser = subparsers.add_parser(
        "adduser",
        parents=[parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_adduser.add_argument("number", nargs="?")
    parser_adduser.add_argument("username", nargs="*")
    parser_adduser.add_argument("--file")
    parser_adduser.set_defaults(func=function)

    function = commands.autoalts
    parser_autoalts = subparsers.add_parser(
        "autoalts",
        parents=[parser_teach],
        aliases="autoalternatives auto-alternatives auto-alts".split(),
        description=function.__doc__,
    )
    parser_autoalts.add_argument("alternative")
    parser_autoalts.set_defaults(func=function)

    function = commands.autoclean
    parser_autoclean = subparsers.add_parser(
        "autoclean",
        parents=[parser_teach],
        aliases=["auto-clean"],
        description=function.__doc__,
    )
    parser_autoclean.set_defaults(func=function)

    function = commands.autodownload
    parser_autodownload = subparsers.add_parser(
        "autodownload",
        aliases=["auto-download"],
        parents=[parser_verbose, parser_yesno, parser_auth, parser_teach],
        description=function.__doc__,
    )
    parser_autodownload.set_defaults(func=function)

    function = commands.autoremove
    parser_autoremove = subparsers.add_parser(
        "autoremove",
        aliases=["auto-remove"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_autoremove.set_defaults(func=function)

    function = commands.build
    parser_build = subparsers.add_parser(
        "build",
        parents=[parser_yesno, parser_auth, parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_build.add_argument("packages", nargs="+")
    parser_build.set_defaults(func=function)

    function = commands.builddeps
    parser_builddeps = subparsers.add_parser(
        "builddeps",
        parents=[parser_yesno, parser_auth, parser_teach],
        aliases="builddepend builddepends build-deps".split(),
        description=function.__doc__,
    )
    parser_builddeps.add_argument("packages", nargs="+")
    parser_builddeps.set_defaults(func=function)

    function = commands.changelog
    parser_changelog = subparsers.add_parser(
        "changelog",
        parents=[parser_verbose, parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_changelog.add_argument("package")
    parser_changelog.set_defaults(func=function)

    function = commands.clean
    parser_clean = subparsers.add_parser(
        "clean",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_clean.set_defaults(func=function)

    function = commands.commands
    parser_commands = subparsers.add_parser(
        "commands",
        aliases="listcommands list-commands".split(),
        parents=[parser_grep],
        description=function.__doc__,
    )
    parser_commands.set_defaults(func=function)

    function = commands.contents
    parser_contents = subparsers.add_parser(
        "contents",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_contents.add_argument("debfile")
    parser_contents.set_defaults(func=function)

    function = commands.dailyupgrade
    parser_dailyupgrade = subparsers.add_parser(
        "dailyupgrade",
        aliases=["daily-upgrade"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_dailyupgrade.set_defaults(func=function)

    # DELUSER
    
    function = commands.deluser
    parser_deluser = subparsers.add_parser(
        "deluser",
        parents=[parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_deluser.add_argument("username", nargs="+")
    parser_deluser.set_defaults(func=function)

    function = commands.dependents
    parser_dependents = subparsers.add_parser(
        "dependents",
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_dependents.add_argument("package")
    parser_dependents.set_defaults(func=function)

    function = commands.describe
    parser_describe = subparsers.add_parser(
        "describe",
        parents=[parser_verbose, parser_teach],
        description=function.__doc__,
    )
    parser_describe.add_argument("packages", nargs="+")
    parser_describe.set_defaults(func=function)

    function = commands.describenew
    parser_describenew = subparsers.add_parser(
        "describenew",
        aliases="newdescribe new-describe describe-new".split(),
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_describenew.set_defaults(func=function)

    function = commands.distupgrade
    parser_distupgrade = subparsers.add_parser(
        "distupgrade",
        aliases=["dist-upgrade", "full-upgrade"],
        parents=[
            parser_backup, parser_yesno, parser_auth, parser_teach,
            parser_local, parser_dist
        ],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=function.__doc__,
    )
    help = "distribution/suite to upgrade to (e.g. unstable)"
    parser_distupgrade.set_defaults(func=function)

    function = commands.download
    parser_download = subparsers.add_parser(
        "download",
        parents=[parser_fileinput, parser_teach],
        description=function.__doc__,
    )
    parser_download.add_argument("packages", nargs="+")
    parser_download.set_defaults(func=function)

    function = commands.editsources
    parser_editsources = subparsers.add_parser(
        "editsources",
        aliases=["edit-sources"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_editsources.set_defaults(func=function)

    function = commands.extract
    parser_extract = subparsers.add_parser(
        "extract",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_extract.add_argument("debfile")
    parser_extract.add_argument("destination_directory")
    parser_extract.set_defaults(func=function)

    function = commands.fixconfigure
    parser_fixconfigure = subparsers.add_parser(
        "fixconfigure",
        aliases=["fix-configure"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_fixconfigure.set_defaults(func=function)

    function = commands.fixinstall
    parser_fixinstall = subparsers.add_parser(
        "fixinstall",
        aliases=["fix-install"],
        parents=[parser_yesno, parser_auth, parser_teach],
        description=function.__doc__,
    )
    parser_fixinstall.set_defaults(func=function)

    function = commands.fixmissing
    parser_fixmissing = subparsers.add_parser(
        "fixmissing",
        aliases=["fix-missing"],
        parents=[parser_yesno, parser_auth, parser_teach],
        description=function.__doc__,
    )
    parser_fixmissing.set_defaults(func=function)

    function = commands.force
    parser_force = subparsers.add_parser(
        "force",
        parents=[parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_force.add_argument("packages", nargs="+")
    parser_force.set_defaults(func=function)

    function = commands.hold
    parser_hold = subparsers.add_parser(
        "hold",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_hold.add_argument("packages", nargs="+")
    parser_hold.set_defaults(func=function)

    function = commands.info
    parser_info = subparsers.add_parser(
        "info",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_info.add_argument("package")
    parser_info.set_defaults(func=function)

    function = commands.init
    parser_init = subparsers.add_parser(
        "init",
        description=function.__doc__,
    )
    parser_init.set_defaults(func=function)

    function = commands.install
    parser_install = subparsers.add_parser(
        "install",
        parents=[
            parser_recommends, parser_yesno, parser_auth, parser_dist,
            parser_fileinput, parser_teach
        ],
        aliases="isntall autoinstall".split(),
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_install.add_argument("packages", nargs="+")
    parser_install.set_defaults(func=function)

    function = commands.installsuggested
    parser_installsuggested = subparsers.add_parser(
        "installsuggested",
        parents=[
            parser_recommends, parser_yesno, parser_auth, parser_dist,
            parser_teach
        ],
        aliases="installs suggested install-suggested".split(),
        description=function.__doc__,
    )
    parser_installsuggested.add_argument("package")
    parser_installsuggested.set_defaults(func=function)

    function = commands.integrity
    parser_integrity = subparsers.add_parser(
        "integrity",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_integrity.set_defaults(func=function)

    function = commands.large
    parser_large = subparsers.add_parser(
        "large",
        description=function.__doc__,
    )
    parser_large.set_defaults(func=function)

    function = commands.lastupdate
    parser_lastupdate = subparsers.add_parser(
        "lastupdate",
        aliases=["last-update"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_lastupdate.set_defaults(func=function)

    function = commands.listalternatives
    parser_listalternatives = subparsers.add_parser(
        "listalternatives",
        parents=[parser_teach],
        aliases="listalts list-alternatives".split(),
        description=function.__doc__,
    )
    parser_listalternatives.set_defaults(func=function)

    function = commands.listall
    parser_listall = subparsers.add_parser(
        "listall",
        aliases=["list-all"],
        parents=[parser_teach, parser_grep],
        description=function.__doc__,
    )
    parser_listall.set_defaults(func=function)

    function = commands.listcache
    parser_listcache = subparsers.add_parser(
        "listcache",
        aliases=["list-cache"],
        parents=[parser_teach, parser_grep],
        description=function.__doc__,
    )
    parser_listcache.set_defaults(func=function)

    function = commands.listdaemons
    parser_listdaemons = subparsers.add_parser(
        "listdaemons",
        aliases=["list-daemons"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_listdaemons.set_defaults(func=function)

    function = commands.listfiles
    parser_listfiles = subparsers.add_parser(
        "listfiles",
        aliases=["list-files"],
        description=function.__doc__,
    )
    parser_listfiles.add_argument("package")
    parser_listfiles.set_defaults(func=function)

    function = commands.listhold
    parser_listhold = subparsers.add_parser(
        "listhold",
        aliases=["list-hold"],
        description=function.__doc__,
    )
    parser_listhold.set_defaults(func=function)

    function = commands.listinstalled
    parser_listinstalled = subparsers.add_parser(
        "listinstalled",
        aliases=["list-installed"],
        parents=[parser_teach, parser_grep],
        description=function.__doc__,
    )
    parser_listinstalled.set_defaults(func=function)

    function = commands.listnames
    parser_listnames = subparsers.add_parser(
        "listnames",
        aliases=["list-names"],
        parents=[parser_teach, parser_grep],
        description=function.__doc__,
    )
    parser_listnames.set_defaults(func=function)

    function = commands.listpackages
    parser_listpackages = subparsers.add_parser(
        "listpackages",
        parents=[parser_teach, parser_grep],
        aliases="list list-packages".split(),
        description=function.__doc__,
    )
    parser_listpackages.set_defaults(func=function)

    function = commands.listscripts
    parser_listscripts = subparsers.add_parser(
        "listscripts",
        aliases=["list-scripts"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_listscripts.add_argument("debfile")
    parser_listscripts.set_defaults(func=function)

    function = commands.listsection
    parser_listsection = subparsers.add_parser(
        "listsection",
        aliases=["list-section"],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_listsection.add_argument("section")
    parser_listsection.set_defaults(func=function)

    function = commands.listsections
    parser_listsections = subparsers.add_parser(
        "listsections",
        aliases=["list-sections"],
        description=function.__doc__,
    )
    parser_listsections.set_defaults(func=function)

    function = commands.liststatus
    parser_liststatus = subparsers.add_parser(
        "liststatus",
        aliases=["list-status"],
        parents=[parser_teach, parser_grep],
        description=function.__doc__,
    )
    parser_liststatus.set_defaults(func=function)

    function = commands.madison
    parser_madison = subparsers.add_parser(
        "madison",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_madison.add_argument("packages", nargs="+")
    parser_madison.set_defaults(func=function)

    function = commands.move
    parser_move = subparsers.add_parser(
        "move",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_move.set_defaults(func=function)

    function = commands.new
    parser_new = subparsers.add_parser(
        "new",
        parents=[parser_verbose],
        description=function.__doc__,
    )
    parser_new.set_defaults(func=function)

    function = commands.newdetail
    parser_newdetail = subparsers.add_parser(
        "newdetail",
        aliases="detailnew detail-new new-detail".split(),
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_newdetail.set_defaults(func=function)

    function = commands.news
    parser_news = subparsers.add_parser(
        "news",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_news.add_argument("package")
    parser_news.set_defaults(func=function)

    function = commands.nonfree
    parser_nonfree = subparsers.add_parser(
        "nonfree",
        aliases=["non-free"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_nonfree.set_defaults(func=function)

    function = commands.orphans
    parser_orphans = subparsers.add_parser(
        "orphans",
        parents=[parser_teach],
        aliases="orphaned listorphaned listorphans".split(),
        description=function.__doc__,
    )
    parser_orphans.set_defaults(func=function)

    # PASSWORD
    
    function = commands.password
    parser_password = subparsers.add_parser(
        "password",
        parents=[parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_password.add_argument("-p", "--punct", action='store_true')
    parser_password.add_argument("number", nargs="?")
    parser_password.add_argument("length", nargs="?")
    parser_password.set_defaults(func=function)

    function = commands.policy
    parser_policy = subparsers.add_parser(
        "policy",
        parents=[parser_teach],
        aliases=["available"],
        description=function.__doc__,
    )
    parser_policy.add_argument("packages", nargs="+")
    parser_policy.set_defaults(func=function)

    function = commands.purge
    parser_purge = subparsers.add_parser(
        "purge",
        aliases=["purgedepend"],
        parents=[parser_yesno, parser_auth, parser_fileinput, parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_purge.add_argument("packages", nargs="+")
    parser_purge.set_defaults(func=function)

    function = commands.purgeorphans
    parser_purgeorphans = subparsers.add_parser(
        "purgeorphans",
        aliases=["purge-orphans"],
        parents=[parser_yesno],
        description=function.__doc__,
    )
    parser_purgeorphans.set_defaults(func=function)

    function = commands.purgeremoved
    parser_purgeremoved = subparsers.add_parser(
        "purgeremoved",
        aliases=["purge-removed"],
        description=function.__doc__,
    )
    parser_purgeremoved.set_defaults(func=function)

    function = commands.rbuilddeps
    parser_rbuilddeps = subparsers.add_parser(
        "rbuilddeps",
        parents=[parser_teach],
        aliases="rbuilddep reversebuilddeps reverse-build-deps".split(),
        description=function.__doc__,
    )
    parser_rbuilddeps.add_argument("package")
    parser_rbuilddeps.set_defaults(func=function)

    # README
    
    function = commands.readme
    parser_readme = subparsers.add_parser(
        "readme",
        parents=[parser_teach],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=function.__doc__,
    )
    parser_readme.add_argument("package")
    parser_readme.set_defaults(func=function)

    # REBOOT
    
    function = commands.reboot
    parser_reboot = subparsers.add_parser(
        "reboot",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_reboot.set_defaults(func=function)

    function = commands.recdownload
    parser_recdownload = subparsers.add_parser(
        "recdownload",
        parents=[parser_auth, parser_teach],
        aliases="recursive rec-download".split(),
        description=function.__doc__,
    )
    parser_recdownload.add_argument("packages", nargs="+")
    parser_recdownload.set_defaults(func=function)

    function = commands.recommended
    parser_recommended = subparsers.add_parser(
        "recommended",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_recommended.set_defaults(func=function)

    function = commands.reconfigure
    parser_reconfigure = subparsers.add_parser(
        "reconfigure",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_reconfigure.add_argument("packages", nargs="+")
    parser_reconfigure.set_defaults(func=function)

    function = commands.reinstall
    parser_reinstall = subparsers.add_parser(
        "reinstall",
        aliases=["re-install"],
        parents=[parser_yesno, parser_auth, parser_teach],
        description=function.__doc__,
    )
    parser_reinstall.add_argument("packages", nargs="+")
    parser_reinstall.set_defaults(func=function)

    function = commands.reload
    parser_reload = subparsers.add_parser(
        "reload",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_reload.add_argument("daemon")
    parser_reload.set_defaults(func=function)

    function = commands.remove
    parser_remove = subparsers.add_parser(
        "remove",
        parents=[parser_yesno, parser_auth, parser_fileinput, parser_teach],
        description=function.__doc__,
    )
    parser_remove.add_argument("packages", nargs="+")
    parser_remove.set_defaults(func=function)

    function = commands.removeorphans
    parser_removeorphans = subparsers.add_parser(
        "removeorphans",
        aliases=["remove-orphans"],
        parents=[parser_yesno],
        description=function.__doc__,
    )
    parser_removeorphans.set_defaults(func=function)

    function = commands.repackage
    parser_repackage = subparsers.add_parser(
        "repackage",
        parents=[parser_teach],
        aliases=["package"],
        description=function.__doc__,
    )
    parser_repackage.add_argument("package")
    parser_repackage.set_defaults(func=function)

    function = commands.reportbug
    parser_reportbug = subparsers.add_parser(
        "reportbug",
        parents=[parser_teach],
        aliases="bug bugreport".split(),
        description=function.__doc__,
    )
    parser_reportbug.add_argument("package")
    parser_reportbug.set_defaults(func=function)

    function = commands.restart
    parser_restart = subparsers.add_parser(
        "restart",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_restart.add_argument("daemon")
    parser_restart.set_defaults(func=function)

    function = commands.rpm2deb
    parser_rpm2deb = subparsers.add_parser(
        "rpm2deb",
        parents=[parser_teach],
        aliases=["rpmtodeb"],
        description=function.__doc__,
    )
    parser_rpm2deb.add_argument("rpm")
    parser_rpm2deb.set_defaults(func=function)

    function = commands.rpminstall
    parser_rpminstall = subparsers.add_parser(
        "rpminstall",
        aliases=["rpm-install"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_rpminstall.add_argument("rpm")
    parser_rpminstall.set_defaults(func=function)

    function = commands.search
    parser_search = subparsers.add_parser(
        "search",
        parents=[parser_teach],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_search.add_argument("patterns", nargs="+")
    help = (
        "'-v' will also search short package desciption; "
        "'-vv' will also search the short and long decription"
    )
    parser_search.add_argument("-v", "--verbose", action="count", help=help)
    parser_search.set_defaults(func=function)

    function = commands.searchapt
    parser_searchapt = subparsers.add_parser(
        "searchapt",
        parents=[parser_teach],
        aliases=["search-apt"],
        description=function.__doc__,
    )
    parser_searchapt.add_argument("dist")
    parser_searchapt.set_defaults(func=function)

    function = commands.show
    parser_show = subparsers.add_parser(
        "show",
        parents=[parser_fast, parser_teach],
        aliases="detail details".split(),
        description=function.__doc__,
    )
    parser_show.add_argument("packages", nargs="+")
    parser_show.set_defaults(func=function)

    function = commands.sizes
    parser_sizes = subparsers.add_parser(
        "sizes",
        parents=[parser_teach],
        aliases=["size"],
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_sizes.add_argument("packages", nargs="*")
    parser_sizes.set_defaults(func=function)

    function = commands.snapshot
    parser_snapshot = subparsers.add_parser(
        "snapshot",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_snapshot.set_defaults(func=function)

    function = commands.source
    parser_source = subparsers.add_parser(
        "source",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_source.add_argument("packages", nargs="+")
    parser_source.set_defaults(func=function)

    function = commands.start
    parser_start = subparsers.add_parser(
        "start",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_start.add_argument("daemon")
    parser_start.set_defaults(func=function)

    # STATUS
    
    function = commands.status
    parser_status = subparsers.add_parser(
        "status",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_status.add_argument("pattern", nargs="+")
    parser_status.set_defaults(func=function)

    # STOP
    
    function = commands.stop
    parser_stop = subparsers.add_parser(
        "stop",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_stop.add_argument("daemon")
    parser_stop.set_defaults(func=function)

    # SYSINFO
    
    function = commands.sysinfo
    parser_sysinfo = subparsers.add_parser(
        "sysinfo",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_sysinfo.set_defaults(func=function)

    function = commands.aptlog
    parser_aptlog = subparsers.add_parser(
        "aptlog",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_aptlog.set_defaults(func=function)

    function = commands.listlog
    parser_listlog = subparsers.add_parser(
        "listlog",
        aliases=["list-log"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_listlog.set_defaults(func=function)

    function = commands.tasksel
    parser_tasksel = subparsers.add_parser(
        "tasksel",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_tasksel.set_defaults(func=function)

    function = commands.todo
    parser_todo = subparsers.add_parser(
        "todo",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_todo.add_argument("package")
    parser_todo.set_defaults(func=function)

    function = commands.toupgrade
    parser_toupgrade = subparsers.add_parser(
        "toupgrade",
        aliases="newupgrades new-upgrades to-upgrade".split(),
        description=function.__doc__,
    )
    parser_toupgrade.set_defaults(func=function)

    function = commands.tutorial
    parser_tutorial = subparsers.add_parser(
        "tutorial",
        aliases="doc docs documentation".split(),
        description=function.__doc__,
    )
    parser_tutorial.set_defaults(func=function)

    function = commands.unhold
    parser_unhold = subparsers.add_parser(
        "unhold",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_unhold.add_argument("packages", nargs="+")
    parser_unhold.set_defaults(func=function)

    function = commands.unofficial
    parser_unofficial = subparsers.add_parser(
        "unofficial",
        parents=[parser_teach],
        aliases="findpkg findpackage".split(),
        description=function.__doc__,
    )
    parser_unofficial.add_argument("package")
    parser_unofficial.set_defaults(func=function)

    function = commands.update
    parser_update = subparsers.add_parser(
        "update",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_update.set_defaults(func=function)

    function = commands.updatealternatives
    parser_updatealternatives = subparsers.add_parser(
        "updatealternatives",
        parents=[parser_teach],
        aliases=("updatealts update-alts setalts set-alts setalternatives"
                 "set-alternatives update-alternatives").split(),
        description=function.__doc__,
    )
    parser_updatealternatives.add_argument("alternative")
    parser_updatealternatives.set_defaults(func=function)

    function = commands.updatepciids
    parser_updatepciids = subparsers.add_parser(
        "updatepciids",
        aliases="update-pciids update-pci-ids".split(),
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_updatepciids.set_defaults(func=function)

    function = commands.updateusbids
    parser_updateusbids = subparsers.add_parser(
        "updateusbids",
        aliases="update-usbids update-usb-ids".split(),
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_updateusbids.set_defaults(func=function)

    function = commands.upgrade
    parser_upgrade = subparsers.add_parser(
        "upgrade",
        parents=[parser_backup, parser_yesno, parser_auth, parser_teach,
                 parser_local],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=function.__doc__,
    )
    parser_upgrade.set_defaults(func=function)

    function = commands.upgradesecurity
    parser_upgradesecurity = subparsers.add_parser(
        "upgradesecurity",
        aliases=["upgrade-security"],
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_upgradesecurity.set_defaults(func=function)

    function = commands.verify
    parser_verify = subparsers.add_parser(
        "verify",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_verify.add_argument("package")
    parser_verify.set_defaults(func=function)

    # VERSION
    
    function = commands.version
    parser_version = subparsers.add_parser(
        "version",
        description=function.__doc__,
    )
    parser_version.set_defaults(func=function)

    # VERSIONS
    
    function = commands.versions
    parser_versions = subparsers.add_parser(
        "versions",
        parents=[parser_teach],
        description=function.__doc__,
    )
    parser_versions.add_argument("packages", nargs="*")
    parser_versions.set_defaults(func=function)

    # WHICHPKG
    
    function = commands.whichpackage
    parser_whichpackage = subparsers.add_parser(
        "whichpackage",
        aliases=("findfile find-file locate filesearch file-search whichpkg "
                 "which-package").split(),
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser_whichpackage.add_argument("pattern", help="partial/full file path")
    parser_whichpackage.set_defaults(func=function)

    #-----------------------------------------------------------------------
    # HANDLE FUZZY COMMANDS
    #-----------------------------------------------------------------------
    
    # Get the first positional argument - the command - and consider replacing.
    
    pos_args = [(i, arg) for i, arg in enumerate(sys.argv[1:]) if not arg.startswith('-')]
    cmd_index, cmd = pos_args[0] if len(pos_args) != 0 else (None, None)
    if cmd:
        choices = commands.commands(None, True)
        matched_cmd = util.get_misspelled_command(cmd, choices)
        if matched_cmd is not None:
            sys.argv[cmd_index + 1] = matched_cmd

    #-----------------------------------------------------------------------
    # PARSE COMMAND LINE
    #-----------------------------------------------------------------------

    result = parser.parse_args()

    try:
        result.recommends = "--install-recommends" if result.recommends else ""
    except AttributeError:
        pass
    try:
        result.local = "--no-download --ignore-missing" if result.local else ""
    except AttributeError:
        pass
    try:
        result.recommends = "--no-install-recommends" if result.norecommends else ""
    except AttributeError:
        pass
    try:
        if not result.dist:
            result.dist = ""
    except AttributeError:
        pass
    try:
        result.noauth = " --allow-unauthenticated " if result.noauth else ""
    except AttributeError:
        pass
    try:
        result.yes = " --yes " if result.yes else ""
    except AttributeError:
        pass

    result.func(result)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
