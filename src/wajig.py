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

import argparse
import sys

# local modules
import commands
import changes
import util
import const


def main():

    # before we do any other command make sure the right files exist
    changes.ensure_initialised()

    # without arguments, run a wajig shell (interactive mode)
    if len(sys.argv) == 1:
        import subprocess
        command = "python3 /usr/share/wajig/shell.py"
        subprocess.call(command.split())
        return

    # if only argparse would have me avoid this hack
    for n, arg in enumerate(sys.argv):
        if arg not in ["-V", "-R"]:
            sys.argv[n] = arg.lower()

    parser = argparse.ArgumentParser(
        prog="wajig",
        description="unified package management front-end for Debian",
        epilog=("'wajig commands' displays available commands\n"
                "'wajig doc' displays a tutorial"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser_backup = argparse.ArgumentParser(add_help=False)
    message = ("backup packages currently installed packages before replacing "
               "them; used in conjuntion with [DIST]UPGRADE commands")
    parser_backup.add_argument("-b", "--backup", action='store_true',
                                help=message)

    parser_verbose = argparse.ArgumentParser(add_help=False)
    message = ("turn on verbose output")
    parser_verbose.add_argument("-v", "--verbose", action="store_true",
                                help=message)

    parser_fast = argparse.ArgumentParser(add_help=False)
    message = ("uses the faster apt-cache instead of the slower (but more "
               "advanced) aptitude to display package info; used in "
               "conjunction with SHOW command")
    parser_fast.add_argument("-f", "--fast", action='store_true', help=message)

    parser_recommends = argparse.ArgumentParser(add_help=False)
    message = ("install with Recommended dependencies; used in "
               "conjunction with INSTALL command")
    parser_recommends.add_argument("-r", "--recommends", action='store_true',
                                    default=True, help=message)
    message = ("do not install with Recommended dependencies; used in "
               "conjunction with INSTALL command")
    parser_recommends.add_argument("-R", "--norecommends",
                                     action='store_false', help=message)

    parser_yesno = argparse.ArgumentParser(add_help=False)
    message = "skip 'Yes/No' confirmation prompts; use with care!"
    parser_yesno.add_argument("-y", "--yes", action='store_true', help=message)

    parser_auth = argparse.ArgumentParser(add_help=False)
    message = "do not authenticate packages before installation"
    parser_auth.add_argument("-n", "--noauth", action='store_true', help=message)

    parser_dist = argparse.ArgumentParser(add_help=False)
    message = "specify a distribution to use (e.g. testing or experimental)"
    parser_dist.add_argument("-d", "--dist", help=message)

    parser_install = argparse.ArgumentParser(add_help=False)
    message = "install the newly-available packages"
    parser_install.add_argument("-i", "--install", action="store_true",
                                 help=message)

    message = "show wajig version"
    parser.add_argument("-V", "--version", action="version", help=message,
                        version="%(prog)s " + const.version)

    subparsers = parser.add_subparsers(title='subcommands',
                                       help=argparse.SUPPRESS)

    def help(args):
        args.parser.print_help()
    parser_help = subparsers.add_parser("help")
    parser_help.set_defaults(func=help, parser=parser)

    function = commands.addcdrom
    parser_addcdrom = subparsers.add_parser("addcdrom",
                      description=function.__doc__,
                      epilog="runs 'apt-cdrom add'")
    parser_addcdrom.set_defaults(func=function)

    function = commands.addrepo
    parser_addrepo = subparsers.add_parser("addrepo",
                     description=function.__doc__,
                     epilog="runs 'add-apt-repository'",
                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_addrepo.add_argument("ppa")
    parser_addrepo.set_defaults(func=function)

    function = commands.autoalts
    parser_autoalts = subparsers.add_parser("autoalts",
                      aliases=["autoalternatives"],
                      description=function.__doc__,
                      epilog="runs 'update-alternatives --auto'")
    parser_autoalts.add_argument("alternative")
    parser_autoalts.set_defaults(func=function)

    function = commands.autoclean
    parser_autoclean = subparsers.add_parser("autoclean",
                       description=function.__doc__,
                       epilog="runs 'apt-get autoclean'")
    parser_autoclean.set_defaults(func=function)

    function = commands.autodownload
    parser_autodownload = subparsers.add_parser("autodownload",
        parents=[parser_verbose, parser_yesno, parser_auth, parser_install],
        description=function.__doc__,
        epilog=("runs 'apt-get --download-only --assume-yes "
                "--show-upgraded dist-upgrade'"))
    parser_autodownload.set_defaults(func=function)

    function = commands.autoremove
    parser_autoremove = subparsers.add_parser("autoremove",
                        description=function.__doc__)
    parser_autoremove.set_defaults(func=function)

    function = commands.build
    parser_build = subparsers.add_parser("build",
                   parents=[parser_yesno, parser_auth],
                   description=function.__doc__,
                   epilog="runs 'apt-get build-dep && apt-get source --build'")
    parser_build.add_argument("packages", nargs="+")
    parser_build.set_defaults(func=function)

    function = commands.builddeps
    parser_builddeps = subparsers.add_parser("builddeps",
                       parents=[parser_yesno, parser_auth],
                       aliases="builddepend builddepends".split(),
                       epilog="runs 'apt-get build-dep'",
                       description=function.__doc__)
    parser_builddeps.add_argument("packages", nargs="+")
    parser_builddeps.set_defaults(func=function)

    function = commands.changelog
    parser_changelog = subparsers.add_parser("changelog",
                       parents=[parser_verbose],
                       description=function.__doc__,
                       formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_changelog.add_argument("package")
    parser_changelog.set_defaults(func=function)

    function = commands.clean
    parser_clean = subparsers.add_parser("clean",
                   description=function.__doc__,
                   epilog="runs 'apt-get clean'")
    parser_clean.set_defaults(func=function)

    function = commands.listcommands
    parser_commands = subparsers.add_parser("listcommands",
                      aliases=["commands"],
                      description=function.__doc__)
    parser_commands.set_defaults(func=function)

    function = commands.contents
    parser_contents = subparsers.add_parser("contents",
                      description=function.__doc__,
                      epilog="runs 'dpkg --contents'")
    parser_contents.add_argument("debfile")
    parser_contents.set_defaults(func=function)

    function = commands.dailyupgrade
    parser_dailyupgrade = subparsers.add_parser("dailyupgrade",
                          description=function.__doc__,
                          epilog="runs 'apt-get --show-upgraded dist-upgrade'")
    parser_dailyupgrade.set_defaults(func=function)

    function = commands.dependents
    parser_dependents = subparsers.add_parser("dependents",
                        description=function.__doc__,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_dependents.add_argument("package")
    parser_dependents.set_defaults(func=function)

    function = commands.describe
    parser_describe = subparsers.add_parser("describe",
                      parents=[parser_verbose],
                      description=function.__doc__)
    parser_describe.add_argument("packages", nargs="+")
    parser_describe.set_defaults(func=function)

    function = commands.describenew
    parser_describenew = subparsers.add_parser("describenew",
                         parents=[parser_verbose],
                         aliases=["newdescribe"],
                         description=function.__doc__)
    parser_describenew.set_defaults(func=function)

    function = commands.distupgrade
    parser_distupgrade = subparsers.add_parser("distupgrade",
                         parents=[parser_backup, parser_yesno, parser_auth],
                         description=function.__doc__,
                         epilog="runs 'apt-get --show-upgraded distupgrade'")
    help = "distribution/suite to upgrade to (e.g. unstable)"
    parser_distupgrade.add_argument("dist", nargs="*", help=help)
    parser_distupgrade.set_defaults(func=function)

    function = commands.download
    parser_download = subparsers.add_parser("download",
                  description=function.__doc__,
                  epilog="runs 'apt-get --reinstall --download-only install'")
    parser_download.add_argument("packages", nargs="+")
    parser_download.set_defaults(func=function)

    function = commands.editsources
    parser_editsources = subparsers.add_parser("editsources",
                         description=function.__doc__,
                         epilog="runs 'editor /etc/apt/sources.list'")
    parser_editsources.set_defaults(func=function)

    function = commands.extract
    parser_extract = subparsers.add_parser("extract",
                     description=function.__doc__)
    parser_extract.add_argument("debfile")
    parser_extract.add_argument("destination_directory")
    parser_extract.set_defaults(func=function)

    function = commands.fixconfigure
    parser_fixconfigure = subparsers.add_parser("fixconfigure",
                       description=function.__doc__,
                       epilog="runs 'dpkg --configure --pending'")
    parser_fixconfigure.set_defaults(func=function)

    function = commands.fixinstall
    parser_fixinstall = subparsers.add_parser("fixinstall",
                        parents=[parser_yesno, parser_auth],
                        description=function.__doc__,
                        epilog="runs 'apt-get --fix-broken install")
    parser_fixinstall.set_defaults(func=function)

    function = commands.fixmissing
    parser_fixmissing = subparsers.add_parser("fixmissing",
                        parents=[parser_yesno, parser_auth],
                        description=function.__doc__,
                        epilog="runs 'apt-get --ignore-missing'")
    parser_fixmissing.set_defaults(func=function)

    function = commands.force
    parser_force = subparsers.add_parser("force",
                   description=function.__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_force.add_argument("packages", nargs="+")
    parser_force.set_defaults(func=function)

    function = commands.hold
    parser_hold = subparsers.add_parser("hold",
                       description=function.__doc__)
    parser_hold.add_argument("packages", nargs="+")
    parser_hold.set_defaults(func=function)

    function = commands.info
    parser_info = subparsers.add_parser("info",
                  description=function.__doc__,
                  epilog="runs 'dpkg --info'")
    parser_info.add_argument("package")
    parser_info.set_defaults(func=function)

    function = commands.init
    parser_init = subparsers.add_parser("init",
                  description=function.__doc__)
    parser_init.set_defaults(func=function)

    function = commands.install
    parser_installer = subparsers.add_parser("install",
        parents=[parser_recommends, parser_yesno, parser_auth, parser_dist],
        aliases="isntall autoinstall".split(),
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_installer.add_argument("packages", nargs="+")
    parser_installer.add_argument("-f", "--fileinput", action="store_true",
        help=("if any of the arguments are files, assume contents to be "
              "packages names"))
    parser_installer.set_defaults(func=function)

    function = commands.installsuggested
    parser_installsuggested = subparsers.add_parser("installsuggested",
        parents=[parser_recommends, parser_yesno, parser_auth, parser_dist],
        aliases="installs suggested".split(),
        description=function.__doc__)
    parser_installsuggested.add_argument("package")
    parser_installsuggested.set_defaults(func=function)

    function = commands.integrity
    parser_integrity = subparsers.add_parser("integrity",
                       description=function.__doc__,
                       epilog="runs 'debsums --all --silent'")
    parser_integrity.set_defaults(func=function)

    function = commands.large
    parser_large = subparsers.add_parser("large",
                   description=function.__doc__)
    parser_large.set_defaults(func=function)

    function = commands.lastupdate
    parser_lastupdate = subparsers.add_parser("lastupdate",
                        description=function.__doc__)
    parser_lastupdate.set_defaults(func=function)

    function = commands.listalternatives
    parser_listalternatives = subparsers.add_parser("listalternatives",
                              aliases=["listalts"],
                              description=function.__doc__)
    parser_listalternatives.set_defaults(func=function)

    function = commands.listcache
    parser_listcache = subparsers.add_parser("listcache",
                       description=function.__doc__)
    parser_listcache.set_defaults(func=function)

    function = commands.listdaemons
    parser_listdaemons = subparsers.add_parser("listdaemons",
                         description=function.__doc__)
    parser_listdaemons.set_defaults(func=function)

    function = commands.listfiles
    parser_listfiles = subparsers.add_parser("listfiles",
                       description=function.__doc__)
    parser_listfiles.add_argument("package")
    parser_listfiles.set_defaults(func=function)

    function = commands.listhold
    parser_listhold = subparsers.add_parser("listhold",
                       description=function.__doc__)
    parser_listhold.set_defaults(func=function)

    function = commands.listinstalled
    parser_listinstalled = subparsers.add_parser("listinstalled",
                           description=function.__doc__)
    parser_listinstalled.set_defaults(func=function)

    function = commands.listnames
    parser_listnames = subparsers.add_parser("listnames",
                       description=function.__doc__)
    parser_listnames.set_defaults(func=function)

    function = commands.listpackages
    parser_listpackages = subparsers.add_parser("listpackages",
                          aliases=["list"],
                          description=function.__doc__)
    parser_listpackages.set_defaults(func=function)

    function = commands.listscripts
    parser_listscripts = subparsers.add_parser("listscripts",
                         description=function.__doc__)
    parser_listscripts.add_argument("debfile")
    parser_listscripts.set_defaults(func=function)

    function = commands.listsection
    parser_listsection = subparsers.add_parser("listsection",
                         description=function.__doc__,
                         formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_listsection.add_argument("section")
    parser_listsection.set_defaults(func=function)

    function = commands.listsections
    parser_listsections = subparsers.add_parser("listsections",
                          description=function.__doc__)
    parser_listsections.set_defaults(func=function)

    function = commands.liststatus
    parser_liststatus = subparsers.add_parser("liststatus",
                        description=function.__doc__)
    parser_liststatus.set_defaults(func=function)

    function = commands.localdistupgrade
    parser_localdistupgrade = subparsers.add_parser("localdistupgrade",
        description=function.__doc__,
        epilog=("apt-get --no-download --ignore-missing --show-upgraded "
                "dist-upgrade"))
    parser_localdistupgrade.set_defaults(func=function)

    function = commands.localupgrade
    parser_localupgrade = subparsers.add_parser("localupgrade",
                          description=function.__doc__)
    parser_localupgrade.set_defaults(func=function)

    function = commands.madison
    parser_madison = subparsers.add_parser("madison",
                     description=function.__doc__,
                     epilog="runs 'apt-cache madison'")
    parser_madison.add_argument("packages", nargs="+")
    parser_madison.set_defaults(func=function)

    function = commands.move
    parser_move = subparsers.add_parser("move",
                  description=function.__doc__)
    parser_move.set_defaults(func=function)

    function = commands.new
    parser_new = subparsers.add_parser("new",
                 parents=[parser_install],
                 description=function.__doc__)
    parser_new.set_defaults(func=function)

    function = commands.newdetail
    parser_newdetail = subparsers.add_parser("newdetail",
                       parents=[parser_fast],
                       aliases=["detailnew"],
                       description=function.__doc__)
    parser_newdetail.set_defaults(func=function)

    function = commands.news
    parser_news = subparsers.add_parser("news",
                  description=function.__doc__)
    parser_news.add_argument("package")
    parser_news.set_defaults(func=function)

    function = commands.newupgrades
    parser_newupgrades = subparsers.add_parser("newupgrades",
                         parents=[parser_yesno, parser_auth, parser_install],
                         description=function.__doc__)
    parser_newupgrades.set_defaults(func=function)

    function = commands.nonfree
    parser_nonfree = subparsers.add_parser("nonfree",
                     description=function.__doc__)
    parser_nonfree.set_defaults(func=function)

    function = commands.orphans
    parser_orphans = subparsers.add_parser("orphans",
                     aliases="orphaned listorphaned listorphans".split(),
                     description=function.__doc__)
    parser_orphans.set_defaults(func=function)

    function = commands.policy
    parser_policy = subparsers.add_parser("policy",
                    aliases=["available"],
                    description=function.__doc__,
                    epilog="runs 'apt-cache policy'")
    parser_policy.add_argument("packages", nargs="+")
    parser_policy.set_defaults(func=function)

    function = commands.purge
    parser_purge = subparsers.add_parser("purge",
                   aliases=["purgedepend"],
                   parents=[parser_yesno, parser_auth],
                   description=function.__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter,
                   epilog="runs 'apt-get --auto-remove purge'")
    parser_purge.add_argument("packages", nargs="+")
    parser_purge.set_defaults(func=function)

    function = commands.purgeorphans
    parser_purgeorphans = subparsers.add_parser("purgeorphans",
                          parents=[parser_yesno, parser_auth],
                          description=function.__doc__)
    parser_purgeorphans.set_defaults(func=function)

    function = commands.purgeremoved
    parser_purgeremoved = subparsers.add_parser("purgeremoved",
                       description=function.__doc__)
    parser_purgeremoved.set_defaults(func=function)

    function = commands.rbuilddeps
    parser_rbuilddeps = subparsers.add_parser("rbuilddeps",
                        aliases="rbuilddep reversebuilddeps".split(),
                        description=function.__doc__)
    parser_rbuilddeps.add_argument("package")
    parser_rbuilddeps.set_defaults(func=function)

    function = commands.readme
    parser_readme = subparsers.add_parser("readme",
                    description=function.__doc__)
    parser_readme.add_argument("package")
    parser_readme.set_defaults(func=function)

    function = commands.recdownload
    parser_recdownload = subparsers.add_parser("recdownload",
                         parents=[parser_auth],
                         aliases=["recursive"],
                         description=function.__doc__)
    parser_recdownload.add_argument("packages", nargs="+")
    parser_recdownload.set_defaults(func=function)

    function = commands.recommended
    parser_recommended = subparsers.add_parser("recommended",
                         description=function.__doc__)
    parser_recommended.set_defaults(func=function)

    function = commands.reconfigure
    parser_reconfigure = subparsers.add_parser("reconfigure",
                         description=function.__doc__,
                         epilog="runs 'dpkg-reconfigure'")
    parser_reconfigure.add_argument("packages", nargs="+")
    parser_reconfigure.set_defaults(func=function)

    function = commands.reinstall
    parser_reinstall = subparsers.add_parser("reinstall",
                       parents=[parser_yesno, parser_auth],
                       description=function.__doc__,
                       epilog="runs 'apt-get install --reinstall'")
    parser_reinstall.add_argument("packages", nargs="+")
    parser_reinstall.set_defaults(func=function)

    function = commands.reload
    parser_reload = subparsers.add_parser("reload",
                    description=function.__doc__,
                    epilog="runs 'service DAEMON reload'")
    parser_reload.add_argument("daemon")
    parser_reload.set_defaults(func=function)

    function = commands.remove
    parser_remove = subparsers.add_parser("remove",
                    parents=[parser_yesno, parser_auth],
                    description=function.__doc__,
                    epilog="runs 'apt-get --auto-remove remove'")
    parser_remove.add_argument("packages", nargs="+")
    parser_remove.set_defaults(func=function)

    function = commands.removeorphans
    parser_removeorphans = subparsers.add_parser("removeorphans",
                           description=function.__doc__)
    parser_removeorphans.set_defaults(func=function)

    function = commands.repackage
    parser_repackage = subparsers.add_parser("repackage",
                       aliases=["package"],
                       description=function.__doc__,
                       epilog="runs 'fakeroot -u dpkg-repack'")
    parser_repackage.add_argument("package")
    parser_repackage.set_defaults(func=function)

    function = commands.reportbug
    parser_reportbug = subparsers.add_parser("reportbug",
                       aliases="bug bugreport".split(),
                       description=function.__doc__,
                       epilog="runs 'reportbug'")
    parser_reportbug.add_argument("package")
    parser_reportbug.set_defaults(func=function)

    function = commands.restart
    parser_restart = subparsers.add_parser("restart",
                     description=function.__doc__,
                     epilog="runs 'service DAEMON restart'")
    parser_restart.add_argument("daemon")
    parser_restart.set_defaults(func=function)

    function = commands.rpm2deb
    parser_rpm2deb = subparsers.add_parser("rpm2deb",
                     aliases=["rpmtodeb"],
                     description=function.__doc__,
                     epilog="runs 'alien'")
    parser_rpm2deb.add_argument("rpm")
    parser_rpm2deb.set_defaults(func=function)

    function = commands.rpminstall
    parser_rpminstall = subparsers.add_parser("rpminstall",
                        description=function.__doc__,
                        epilog="runs 'alien --install'")
    parser_rpminstall.add_argument("rpm")
    parser_rpminstall.set_defaults(func=function)

    function = commands.search
    parser_search = subparsers.add_parser("search",
                                           parents=[parser_verbose],
                                           description=function.__doc__)
    parser_search.add_argument("patterns", nargs="+")
    parser_search.set_defaults(func=function)

    function = commands.searchapt
    parser_searchapt = subparsers.add_parser("searchapt",
                       description=function.__doc__,
                       epilog="runs 'netselect-apt'")
    parser_searchapt.add_argument("dist")
    parser_searchapt.set_defaults(func=function)

    function = commands.show
    parser_show = subparsers.add_parser("show",
                  parents=[parser_fast],
                  aliases="detail details".split(),
                  description=function.__doc__)
    parser_show.add_argument("packages", nargs="+")
    parser_show.set_defaults(func=function)

    function = commands.sizes
    parser_sizes = subparsers.add_parser("sizes",
                   aliases=["size"],
                   description=function.__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_sizes.add_argument("packages", nargs="*")
    parser_sizes.set_defaults(func=function)

    function = commands.snapshot
    parser_snapshot = subparsers.add_parser("snapshot",
                      description=function.__doc__)
    parser_snapshot.set_defaults(func=function)

    function = commands.source
    parser_source = subparsers.add_parser("source",
                    description=function.__doc__,
                    epilog="runs 'apt-get source'")
    parser_source.add_argument("packages", nargs="+")
    parser_source.set_defaults(func=function)

    function = commands.start
    parser_start = subparsers.add_parser("start",
                       description=function.__doc__,
                       epilog="runs 'service DAEMON start'")
    parser_start.add_argument("daemon")
    parser_start.set_defaults(func=function)

    function = commands.status
    parser_status = subparsers.add_parser("status",
                    description=function.__doc__)
    parser_status.add_argument("packages", nargs="+")
    parser_status.set_defaults(func=function)

    function = commands.statusmatch
    parser_statusmatch = subparsers.add_parser("statusmatch",
                         aliases=["statussearch"],
                         description=function.__doc__)
    parser_statusmatch.add_argument("pattern")
    parser_statusmatch.set_defaults(func=function)

    function = commands.stop
    parser_stop = subparsers.add_parser("stop",
                  description=function.__doc__,
                  epilog="runs 'service DAEMON stop'")
    parser_stop.add_argument("daemon")
    parser_stop.set_defaults(func=function)

    function = commands.syslog
    parser_syslog = subparsers.add_parser("syslog",
                    aliases=["listlog"],
                    description=function.__doc__,
                    epilog="runs 'cat /var/log/apt/history.log'")
    parser_syslog.set_defaults(func=function)

    function = commands.tasksel
    parser_tasksel = subparsers.add_parser("tasksel",
                     description=function.__doc__,
                     epilog="runs 'tasksel'")
    parser_tasksel.set_defaults(func=function)

    function = commands.todo
    parser_todo = subparsers.add_parser("todo",
                    description=function.__doc__)
    parser_todo.add_argument("package")
    parser_todo.set_defaults(func=function)

    function = commands.toupgrade
    parser_toupgrade = subparsers.add_parser("toupgrade",
                       description=function.__doc__)
    parser_toupgrade.set_defaults(func=function)

    function = commands.tutorial
    parser_tutorial = subparsers.add_parser("tutorial",
                      aliases="doc docs documentation".split(),
                      description=function.__doc__)
    parser_tutorial.set_defaults(func=function)

    function = commands.unhold
    parser_unhold = subparsers.add_parser("unhold",
                    description=function.__doc__)
    parser_unhold.add_argument("packages", nargs="+")
    parser_unhold.set_defaults(func=function)

    function = commands.unofficial
    parser_unofficial = subparsers.add_parser("unofficial",
                        aliases="findpkg findpackage".split(),
                        description=function.__doc__)
    parser_unofficial.add_argument("package")
    parser_unofficial.set_defaults(func=function)

    function = commands.update
    parser_update = subparsers.add_parser("update",
                    description=function.__doc__)
    parser_update.set_defaults(func=function)

    function = commands.updatealternatives
    parser_updatealternatives = subparsers.add_parser("updatealternatives",
        aliases="updatealts setalts setalternatives".split(),
        description=function.__doc__)
    parser_updatealternatives.add_argument("alternative")
    parser_updatealternatives.set_defaults(func=function)

    function = commands.updatepciids
    parser_updatepciids = subparsers.add_parser("updatepciids",
                       description=function.__doc__,
                       epilog="runs 'update-pciids'")
    parser_updatepciids.set_defaults(func=function)

    function = commands.updateusbids
    parser_updateusbids = subparsers.add_parser("updateusbids",
                          description=function.__doc__)
    parser_updateusbids.set_defaults(func=function)

    function = commands.upgrade
    parser_upgrade = subparsers.add_parser("upgrade",
                     parents=[parser_backup, parser_yesno, parser_auth],
                     description=function.__doc__)
    parser_upgrade.set_defaults(func=function)

    function = commands.upgradesecurity
    parser_upgradesecurity = subparsers.add_parser("upgradesecurity",
                             description=function.__doc__)
    parser_upgradesecurity.set_defaults(func=function)

    function = commands.verify
    parser_verify = subparsers.add_parser("verify",
                    description=function.__doc__)
    parser_verify.add_argument("package")
    parser_verify.set_defaults(func=function)

    function = commands.versions
    parser_versions = subparsers.add_parser("versions",
                      description=function.__doc__,
                      epilog="runs 'apt-show-versions'")
    parser_versions.add_argument("packages", nargs="*")
    parser_versions.set_defaults(func=function)

    function = commands.whichpackage
    parser_whichpackage = subparsers.add_parser("whichpackage",
        aliases="findfile locate filesearch whichpkg".split(),
        description=function.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_whichpackage.add_argument("pattern", help="partial/full file path")
    parser_whichpackage.set_defaults(func=function)

    result = parser.parse_args()
    try:
        util.fast = result.fast
    except AttributeError:
        pass
    try:
        util.recommends_flag = result.recommends
    except AttributeError:
        pass
    try:
        util.recommends_flag = result.norecommends
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
    main()
