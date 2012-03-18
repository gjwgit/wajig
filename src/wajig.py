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

# wajig modules
import commands
import changes
import util
import const


def main():

    # Before we do any other command make sure the right files exist.
    changes.ensure_initialised()

    parser = argparse.ArgumentParser(
        prog="wajig",
        description="""wajig is a simple and unified package management
                       front-end for Debian""",
        epilog="run 'wajig doc | pager' for a tutorial"
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
    message = ("specify a distribution to use (e.g. testing or experimental)")
    parser_dist.add_argument("-d", "--dist", help=message)

    message = "show wajig version"
    parser.add_argument("-V", "--version", action="version", help=message,
                        version="%(prog)s " + const.version)

    subparsers = parser.add_subparsers(title='subcommands',
                                       help='sub-command help')

    function = commands.addcdrom
    summary = function.__doc__
    parser_addcdrom = subparsers.add_parser("addcdrom", help=summary,
                      description=summary,
                      epilog="runs 'apt-cdrom add'")
    parser_addcdrom.set_defaults(func=function)

    function = commands.addrepo
    summary = function.__doc__
    parser_addrepo = subparsers.add_parser("addrepo",
                     help=summary.split("\n")[0],
                     description=summary,
                     epilog="runs 'add-apt-repository'",
                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_addrepo.add_argument("ppa")
    parser_addrepo.set_defaults(func=function)

    function = commands.autoalts
    summary = function.__doc__
    parser_autoalts = subparsers.add_parser("autoalts", help=summary,
                      aliases=["autoalternatives"],
                      description=summary,
                      epilog="runs 'update-alternatives --auto'")
    parser_autoalts.add_argument("alternative")
    parser_autoalts.set_defaults(func=function)

    function = commands.autoclean
    summary = function.__doc__
    parser_autoclean = subparsers.add_parser("autoclean", help=summary,
                       description=summary,
                       epilog="runs 'apt-get autoclean'")
    parser_autoclean.set_defaults(func=function)

    function = commands.autodownload
    summary = function.__doc__
    parser_autodownload = subparsers.add_parser("autodownload", help=summary,
                          parents=[parser_verbose],
                          description=summary,
                          epilog=("runs 'apt-get --download-only --assume-yes "
                                  "--show-upgraded dist-upgrade'"))
    parser_autodownload.set_defaults(func=function)

    function = commands.autoremove
    summary = function.__doc__
    parser_autoremove = subparsers.add_parser("autoremove", help=summary,
                        description=summary)
    parser_autoremove.set_defaults(func=function)

    function = commands.build
    summary = function.__doc__
    parser_build = subparsers.add_parser("build", help=summary,
                   parents=[parser_yesno, parser_auth],
                   description=summary,
                   epilog="runs 'apt-get build-dep && apt-get source --build'")
    parser_build.add_argument("packages", nargs="+")
    parser_build.set_defaults(func=function)

    function = commands.builddeps
    summary = function.__doc__
    parser_builddeps = subparsers.add_parser("builddeps", help=summary,
                       parents=[parser_yesno, parser_auth],
                       aliases="builddepend builddepends".split(),
                       epilog="runs 'apt-get build-dep'",
                       description=summary)
    parser_builddeps.add_argument("packages", nargs="+")
    parser_builddeps.set_defaults(func=function)

    function = commands.changelog
    summary = function.__doc__
    parser_changelog = subparsers.add_parser("changelog", help=summary,
                       parents=[parser_verbose],
                       description=summary,
                       formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_changelog.add_argument("package")
    parser_changelog.set_defaults(func=function)

    function = commands.clean
    summary = function.__doc__
    parser_clean = subparsers.add_parser("clean", help=summary,
                   description=summary,
                   epilog="runs 'apt-get clean'")
    parser_clean.set_defaults(func=function)

    function = commands.contents
    summary = function.__doc__
    parser_contents = subparsers.add_parser("contents", help=summary,
                      description=summary,
                      epilog="runs 'dpkg --contents'")
    parser_contents.add_argument("debfile")
    parser_contents.set_defaults(func=function)

    function = commands.dailyupgrade
    summary = function.__doc__
    parser_dailyupgrade = subparsers.add_parser("dailyupgrade", help=summary,
                          description=summary,
                          epilog="runs 'apt-get --show-upgraded dist-upgrade'")
    parser_dailyupgrade.set_defaults(func=function)

    function = commands.dependents
    summary = function.__doc__
    parser_dependents = subparsers.add_parser("dependents", help=summary,
                        description=summary,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_dependents.add_argument("package")
    parser_dependents.set_defaults(func=function)

    function = commands.describe
    summary = function.__doc__
    parser_describe = subparsers.add_parser("describe", help=summary,
                      parents=[parser_verbose],
                      description=summary)
    parser_describe.add_argument("packages", nargs="+")
    parser_describe.set_defaults(func=function)

    function = commands.describenew
    summary = function.__doc__
    parser_describenew = subparsers.add_parser("describenew", help=summary,
                         parents=[parser_verbose],
                         aliases=["newdescribe"],
                         description=summary)
    parser_describenew.set_defaults(func=function)

    function = commands.distupgrade
    summary = function.__doc__
    parser_distupgrade = subparsers.add_parser("distupgrade", help=summary,
                         parents=[parser_backup, parser_yesno, parser_auth],
                         description=summary,
                         epilog="runs 'apt-get --show-upgraded distupgrade'")
    help="distribution/suite to upgrade to (e.g. unstable)"
    parser_distupgrade.add_argument("dist", nargs="*", help=help)
    parser_distupgrade.set_defaults(func=function)

    function = commands.download
    summary = function.__doc__
    parser_download = subparsers.add_parser("download", help=summary,
                  description=summary,
                  epilog="runs 'apt-get --reinstall --download-only install'")
    parser_download.add_argument("packages", nargs="+")
    parser_download.set_defaults(func=function)

    function = commands.editsources
    summary = function.__doc__
    parser_editsources = subparsers.add_parser("editsources", help=summary,
                         description=summary,
                         epilog="runs 'editor /etc/apt/sources.list'")
    parser_editsources.set_defaults(func=function)

    function = commands.extract
    summary = function.__doc__
    parser_extract = subparsers.add_parser("extract", help=summary,
                     description=summary)
    parser_extract.add_argument("debfile")
    parser_extract.add_argument("destination_directory")
    parser_extract.set_defaults(func=function)

    function = commands.fixconfigure
    summary = function.__doc__
    parser_fixconfigure = subparsers.add_parser("fixconfigure", help=summary,
                       description=summary,
                       epilog="runs 'dpkg --configure --pending'")
    parser_fixconfigure.set_defaults(func=function)

    function = commands.fixinstall
    summary = function.__doc__
    parser_fixinstall = subparsers.add_parser("fixinstall", help=summary,
                        parents=[parser_yesno, parser_auth],
                        description=summary,
                        epilog="runs 'apt-get --fix-broken install")
    parser_fixinstall.set_defaults(func=function)

    function = commands.fixmissing
    summary = function.__doc__
    parser_fixmissing = subparsers.add_parser("fixmissing", help=summary,
                        parents=[parser_yesno, parser_auth],
                        description=summary,
                        epilog="runs 'apt-get --ignore-missing'")
    parser_fixmissing.set_defaults(func=function)

    function = commands.force
    summary = function.__doc__
    parser_force = subparsers.add_parser("force", help=summary,
                   description=summary,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_force.add_argument("packages", nargs="+")
    parser_force.set_defaults(func=function)

    function = commands.hold
    summary = function.__doc__
    parser_hold = subparsers.add_parser("hold", help=summary,
                       description=summary)
    parser_hold.add_argument("packages", nargs="+")
    parser_hold.set_defaults(func=function)

    function = commands.info
    summary = function.__doc__
    parser_info = subparsers.add_parser("info", help=summary,
                  description=summary,
                  epilog="runs 'dpkg --info'")
    parser_info.add_argument("package")
    parser_info.set_defaults(func=function)

    function = commands.init
    summary = function.__doc__
    parser_init = subparsers.add_parser("init", help=summary,
                  description=summary)
    parser_init.set_defaults(func=function)

    function = commands.install
    summary = function.__doc__
    parser_install = subparsers.add_parser("install", help=summary,
        parents=[parser_recommends, parser_yesno, parser_auth, parser_dist],
        aliases="isntall autoinstall".split(),
        description=summary,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_install.add_argument("packages", nargs="+")
    parser_install.set_defaults(func=function)

    function = commands.installsuggested
    summary = function.__doc__
    parser_installsuggested = subparsers.add_parser("installsuggested", help=summary,
        parents=[parser_recommends, parser_yesno, parser_auth, parser_dist],
        aliases="installs suggested".split(),
        description=summary)
    parser_installsuggested.add_argument("package")
    parser_installsuggested.set_defaults(func=function)

    function = commands.integrity
    summary = function.__doc__
    parser_integrity = subparsers.add_parser("integrity", help=summary,
                       description=summary,
                       epilog="runs 'debsums --all --silent'")
    parser_integrity.set_defaults(func=function)

    function = commands.large
    summary = function.__doc__
    parser_large = subparsers.add_parser("large", help=summary,
                   description=summary)
    parser_large.set_defaults(func=function)

    function = commands.lastupdate
    summary = function.__doc__
    parser_lastupdate = subparsers.add_parser("lastupdate", help=summary,
                        description=summary)
    parser_lastupdate.set_defaults(func=function)

    function = commands.listalternatives
    summary = function.__doc__
    parser_listalternatives = subparsers.add_parser("listalternatives",
                              help=summary,
                              aliases=["listalts"],
                              description=summary)
    parser_listalternatives.set_defaults(func=function)

    function = commands.listcache
    summary = function.__doc__
    parser_listcache = subparsers.add_parser("listcache", help=summary,
                       description=summary)
    parser_listcache.set_defaults(func=function)

    function = commands.listdaemons
    summary = function.__doc__
    parser_listdaemons = subparsers.add_parser("listdaemons", help=summary,
                         description=summary)
    parser_listdaemons.set_defaults(func=function)

    function = commands.listfiles
    summary = function.__doc__
    parser_listfiles = subparsers.add_parser("listfiles", help=summary,
                       description=summary)
    parser_listfiles.add_argument("package")
    parser_listfiles.set_defaults(func=function)

    function = commands.listhold
    summary = function.__doc__
    parser_listhold = subparsers.add_parser("listhold", help=summary,
                       description=summary)
    parser_listhold.set_defaults(func=function)

    function = commands.listinstalled
    summary = function.__doc__
    parser_listinstalled = subparsers.add_parser("listinstalled", help=summary,
                           description=summary)
    parser_listinstalled.set_defaults(func=function)

    function = commands.listnames
    summary = function.__doc__
    parser_listnames = subparsers.add_parser("listnames", help=summary,
                       description=summary)
    parser_listnames.set_defaults(func=function)

    function = commands.listpackages
    summary = function.__doc__
    parser_listpackages = subparsers.add_parser("listpackages", help=summary,
                          aliases=["list"],
                          description=summary)
    parser_listpackages.set_defaults(func=function)

    function = commands.listscripts
    summary = function.__doc__
    parser_listscripts = subparsers.add_parser("listscripts", help=summary,
                         description=summary)
    parser_listscripts.add_argument("debfile")
    parser_listscripts.set_defaults(func=function)

    function = commands.listsection
    summary = function.__doc__
    parser_listsection = subparsers.add_parser("listsection", help=summary,
                         description=summary,
                         formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_listsection.add_argument("section")
    parser_listsection.set_defaults(func=function)

    function = commands.listsections
    summary = function.__doc__
    parser_listsections = subparsers.add_parser("listsections", help=summary,
                          description=summary)
    parser_listsections.set_defaults(func=function)

    function = commands.liststatus
    summary = function.__doc__
    parser_liststatus = subparsers.add_parser("liststatus", help=summary,
                        description=summary)
    parser_liststatus.set_defaults(func=function)

    function = commands.localdistupgrade
    summary = function.__doc__
    parser_localdistupgrade = subparsers.add_parser("localdistupgrade",
        help=summary,
        description=summary,
        epilog=("apt-get --no-download --ignore-missing --show-upgraded "
                "dist-upgrade"))
    parser_localdistupgrade.set_defaults(func=function)

    function = commands.localupgrade
    summary = function.__doc__
    parser_localupgrade = subparsers.add_parser("localupgrade", help=summary,
                          description=summary)
    parser_localupgrade.set_defaults(func=function)

    function = commands.madison
    summary = function.__doc__
    parser_madison = subparsers.add_parser("madison", help=summary,
                     description=summary,
                     epilog="runs 'apt-cache madison'")
    parser_madison.add_argument("packages", nargs="+")
    parser_madison.set_defaults(func=function)

    function = commands.move
    summary = function.__doc__
    parser_move = subparsers.add_parser("move", help=summary,
                  description=summary)
    parser_move.set_defaults(func=function)

    function = commands.new
    summary = function.__doc__
    parser_new = subparsers.add_parser("new", help=summary,
                 description=summary)
    parser_new.add_argument("--install", action="store_true",
                            help="install the newly-available packages")
    parser_new.set_defaults(func=function)

    function = commands.newdetail
    summary = function.__doc__
    parser_newdetail = subparsers.add_parser("newdetail", help=summary,
                       parents=[parser_fast],
                       aliases=["detailnew"],
                       description=summary)
    parser_newdetail.set_defaults(func=function)

    function = commands.news
    summary = function.__doc__
    parser_news = subparsers.add_parser("news", help=summary,
                  description=summary)
    parser_news.add_argument("package")
    parser_news.set_defaults(func=function)

    function = commands.newupgrades
    summary = function.__doc__
    parser_newupgrades = subparsers.add_parser("newupgrades", help=summary,
                         parents=[parser_yesno, parser_auth],
                         description=summary)
    parser_newupgrades.add_argument("--install", action="store_true",
        help="install the newly-available packages")
    parser_newupgrades.set_defaults(func=function)

    function = commands.nonfree
    summary = function.__doc__
    parser_nonfree = subparsers.add_parser("nonfree", help=summary,
                     description=summary)
    parser_nonfree.set_defaults(func=function)

    function = commands.orphans
    summary = function.__doc__
    parser_orphans = subparsers.add_parser("orphans", help=summary,
                     aliases="orphaned listorphaned listorphans".split(),
                     description=summary)
    parser_orphans.set_defaults(func=function)

    function = commands.policy
    summary = function.__doc__
    parser_policy = subparsers.add_parser("policy", help=summary,
                    aliases=["available"],
                    description=summary,
                    epilog="runs 'apt-cache policy'")
    parser_policy.add_argument("packages", nargs="+")
    parser_policy.set_defaults(func=function)

    function = commands.purge
    summary = function.__doc__
    parser_purge = subparsers.add_parser("purge", help=summary,
                   aliases=["purgedepend"],
                   parents=[parser_yesno, parser_auth],
                   description=summary,
                   formatter_class=argparse.RawDescriptionHelpFormatter,
                   epilog="runs 'apt-get --auto-remove purge'")
    parser_purge.add_argument("packages", nargs="+")
    parser_purge.set_defaults(func=function)

    function = commands.purgeorphans
    summary = function.__doc__
    parser_purgeorphans = subparsers.add_parser("purgeorphans", help=summary,
                          parents=[parser_yesno, parser_auth],
                          description=summary)
    parser_purgeorphans.set_defaults(func=function)

    function = commands.purgeremoved
    summary = function.__doc__
    parser_purgeremoved = subparsers.add_parser("purgeremoved", help=summary,
                       description=summary)
    parser_purgeremoved.set_defaults(func=function)

    function = commands.rbuilddeps
    summary = function.__doc__
    parser_rbuilddeps = subparsers.add_parser("rbuilddeps", help=summary,
                        aliases="rbuilddep reversebuilddeps".split(),
                        description=summary)
    parser_rbuilddeps.add_argument("package")
    parser_rbuilddeps.set_defaults(func=function)

    function = commands.readme
    summary = function.__doc__
    parser_readme = subparsers.add_parser("readme", help=summary,
                    description=summary)
    parser_readme.add_argument("package")
    parser_readme.set_defaults(func=function)

    function = commands.recdownload
    summary = function.__doc__
    parser_recdownload = subparsers.add_parser("recdownload", help=summary,
                         parents=[parser_auth],
                         aliases=["recursive"],
                         description=summary)
    parser_recdownload.add_argument("packages", nargs="+")
    parser_recdownload.set_defaults(func=function)

    function = commands.recommended
    summary = function.__doc__
    parser_recommended = subparsers.add_parser("recommended", help=summary,
                         description=summary)
    parser_recommended.set_defaults(func=function)

    function = commands.reconfigure
    summary = function.__doc__
    parser_reconfigure = subparsers.add_parser("reconfigure", help=summary,
                         description=summary,
                         epilog="runs 'dpkg-reconfigure'")
    parser_reconfigure.add_argument("packages", nargs="+")
    parser_reconfigure.set_defaults(func=function)

    function = commands.reinstall
    summary = function.__doc__
    parser_reinstall = subparsers.add_parser("reinstall", help=summary,
                       parents=[parser_yesno, parser_auth],
                       description=summary,
                       epilog="runs 'apt-get install --reinstall'")
    parser_reinstall.add_argument("packages", nargs="+")
    parser_reinstall.set_defaults(func=function)

    function = commands.reload
    summary = function.__doc__
    parser_reload = subparsers.add_parser("reload", help=summary,
                    description=summary,
                    epilog="runs 'service DAEMON reload'")
    parser_reload.add_argument("daemon")
    parser_reload.set_defaults(func=function)

    function = commands.remove
    summary = function.__doc__
    parser_remove = subparsers.add_parser("remove", help=summary,
                    parents=[parser_yesno, parser_auth],
                    description=summary,
                    epilog="runs 'apt-get --auto-remove remove'")
    parser_remove.add_argument("packages", nargs="+")
    parser_remove.set_defaults(func=function)

    function = commands.removeorphans
    summary = function.__doc__
    parser_removeorphans = subparsers.add_parser("removeorphans", help=summary,
                           description=summary)
    parser_removeorphans.set_defaults(func=function)

    function = commands.repackage
    summary = function.__doc__
    parser_repackage = subparsers.add_parser("repackage", help=summary,
                       aliases=["package"],
                       description=summary,
                       epilog="runs 'fakeroot -u dpkg-repack'")
    parser_repackage.add_argument("package")
    parser_repackage.set_defaults(func=function)

    function = commands.reportbug
    summary = function.__doc__
    parser_reportbug = subparsers.add_parser("reportbug", help=summary,
                       aliases="bug bugreport".split(),
                       description=summary,
                       epilog="runs 'reportbug'")
    parser_reportbug.add_argument("package")
    parser_reportbug.set_defaults(func=function)

    function = commands.restart
    summary = function.__doc__
    parser_restart = subparsers.add_parser("restart", help=summary,
                     description=summary,
                     epilog="runs 'service DAEMON restart'")
    parser_restart.add_argument("daemon")
    parser_restart.set_defaults(func=function)

    function = commands.rpm2deb
    summary = function.__doc__
    parser_rpm2deb = subparsers.add_parser("rpm2deb", help=summary,
                     aliases=["rpmtodeb"],
                     description=summary,
                     epilog="runs 'alien'")
    parser_rpm2deb.add_argument("rpm")
    parser_rpm2deb.set_defaults(func=function)

    function = commands.rpminstall
    summary = function.__doc__
    parser_rpminstall = subparsers.add_parser("rpminstall", help=summary,
                        description=summary,
                        epilog="runs 'alien --install'")
    parser_rpminstall.add_argument("rpm")
    parser_rpminstall.set_defaults(func=function)

    function = commands.search
    summary = function.__doc__
    parser_search = subparsers.add_parser("search", help=summary,
                                           parents=[parser_verbose],
                                           description=summary)
    parser_search.add_argument("patterns", nargs="+")
    parser_search.set_defaults(func=function)

    function = commands.searchapt
    summary = function.__doc__
    parser_searchapt = subparsers.add_parser("searchapt", help=summary,
                       description=summary,
                       epilog="runs 'netselect-apt'")
    parser_searchapt.add_argument("dist")
    parser_searchapt.set_defaults(func=function)

    function = commands.show
    summary = function.__doc__
    parser_show = subparsers.add_parser("show", help=summary,
                  parents=[parser_fast],
                  aliases="detail details".split(),
                  description=summary)
    parser_show.add_argument("packages", nargs="+")
    parser_show.set_defaults(func=function)

    function = commands.sizes
    summary = function.__doc__
    parser_sizes = subparsers.add_parser("sizes", help=summary,
                   aliases=["size"],
                   description=summary,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_sizes.add_argument("packages", nargs="*")
    parser_sizes.set_defaults(func=function)

    function = commands.snapshot
    summary = function.__doc__
    parser_snapshot = subparsers.add_parser("snapshot", help=summary,
                      description=summary)
    parser_snapshot.set_defaults(func=function)

    function = commands.source
    summary = function.__doc__
    parser_source = subparsers.add_parser("source", help=summary,
                    description=summary,
                    epilog="runs 'apt-get source'")
    parser_source.add_argument("packages", nargs="+")
    parser_source.set_defaults(func=function)

    function = commands.start
    summary = function.__doc__
    parser_start = subparsers.add_parser("start", help=summary,
                       description=summary,
                       epilog="runs 'service DAEMON start'")
    parser_start.add_argument("daemon")
    parser_start.set_defaults(func=function)

    function = commands.status
    summary = function.__doc__
    parser_status = subparsers.add_parser("status", help=summary,
                    description=summary)
    parser_status.add_argument("packages", nargs="+")
    parser_status.set_defaults(func=function)

    function = commands.statusmatch
    summary = function.__doc__
    parser_statusmatch = subparsers.add_parser("statusmatch", help=summary,
                         aliases=["statussearch"],
                         description=summary)
    parser_statusmatch.add_argument("pattern")
    parser_statusmatch.set_defaults(func=function)

    function = commands.stop
    summary = function.__doc__
    parser_stop = subparsers.add_parser("stop", help=summary,
                  description=summary,
                  epilog="runs 'service DAEMON stop'")
    parser_stop.add_argument("daemon")
    parser_stop.set_defaults(func=function)

    function = commands.syslog
    summary = function.__doc__
    parser_syslog = subparsers.add_parser("syslog", help=summary,
                    aliases=["listlog"],
                    description=summary,
                    epilog="runs 'cat /var/log/apt/history.log'")
    parser_syslog.set_defaults(func=function)

    function = commands.tasksel
    summary = function.__doc__
    parser_tasksel = subparsers.add_parser("tasksel", help=summary,
                     description=summary,
                     epilog="runs 'tasksel'")
    parser_tasksel.set_defaults(func=function)

    function = commands.todo
    summary = function.__doc__
    parser_todo = subparsers.add_parser("todo", help=summary,
                    description=summary)
    parser_todo.add_argument("package")
    parser_todo.set_defaults(func=function)

    function = commands.toupgrade
    summary = function.__doc__
    parser_toupgrade = subparsers.add_parser("toupgrade", help=summary,
                       description=summary)
    parser_toupgrade.set_defaults(func=function)

    function = commands.tutorial
    summary = function.__doc__
    parser_tutorial = subparsers.add_parser("tutorial", help=summary,
                      aliases="doc docs documentation".split(),
                      description=summary)
    parser_tutorial.set_defaults(func=function)

    function = commands.unhold
    summary = function.__doc__
    parser_unhold = subparsers.add_parser("unhold", help=summary,
                    description=summary)
    parser_unhold.add_argument("packages", nargs="+")
    parser_unhold.set_defaults(func=function)

    function = commands.unofficial
    summary = function.__doc__
    parser_unofficial = subparsers.add_parser("unofficial", help=summary,
                        aliases="findpkg findpackage".split(),
                        description=summary)
    parser_unofficial.add_argument("package")
    parser_unofficial.set_defaults(func=function)

    function = commands.update
    summary = function.__doc__
    parser_update = subparsers.add_parser("update", help=summary,
                    description=summary)
    parser_update.set_defaults(func=function)

    function = commands.updatealternatives
    summary = function.__doc__
    parser_updatealternatives = subparsers.add_parser("updatealternatives",
        help=summary,
        aliases="updatealts setalts setalternatives".split(),
        description=summary)
    parser_updatealternatives.add_argument("alternative")
    parser_updatealternatives.set_defaults(func=function)

    function = commands.updatepciids
    summary = function.__doc__
    parser_updatepciids = subparsers.add_parser("updatepciids", help=summary,
                       description=summary,
                       epilog="runs 'update-pciids'")
    parser_updatepciids.set_defaults(func=function)

    function = commands.updateusbids
    summary = function.__doc__
    parser_updateusbids = subparsers.add_parser("updateusbids", help=summary,
                          description=summary)
    parser_updateusbids.set_defaults(func=function)

    function = commands.upgrade
    summary = function.__doc__
    parser_upgrade = subparsers.add_parser("upgrade", help=summary,
                     parents=[parser_backup, parser_yesno, parser_auth],
                     description=summary)
    parser_upgrade.set_defaults(func=function)

    function = commands.upgradesecurity
    summary = function.__doc__
    parser_upgradesecurity = subparsers.add_parser("upgradesecurity",
                             help=summary,
                             description=summary)
    parser_upgradesecurity.set_defaults(func=function)

    function = commands.verify
    summary = function.__doc__
    parser_verify = subparsers.add_parser("verify", help=summary,
                    description=summary)
    parser_verify.add_argument("package")
    parser_verify.set_defaults(func=function)

    function = commands.versions
    summary = function.__doc__
    parser_versions = subparsers.add_parser("versions", help=summary,
                      description=summary)
    parser_versions.add_argument("packages", nargs="*")
    parser_versions.set_defaults(func=function)

    function = commands.whichpackage
    summary = function.__doc__
    parser_whichpackage = subparsers.add_parser("whichpackage", help=summary,
        aliases="findfile locate filesearch whichpkg".split(),
        description=summary,
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
