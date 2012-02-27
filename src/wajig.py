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
import os
import subprocess
import sys
import re
import tempfile
import argparse
import textwrap

# wajig modules
import documentation
import commands
import changes
import perform
import util
import const

backup = False
yes = str()
noauth = str()


def wajig_completer(text, state):
    """The start of a completer function. Very rough so far."""
    #
    # Check first that we are completing just the first word.
    # Otherwise do not perform any completion.
    #
    import readline  # To get it in scope.
    current = readline.get_line_buffer()
    if len(current.split()) > 1 or current[-1] == ' ':
        return None
    #
    # Complete the command.
    #
    global match_commands  # List of cached matching commands
    n = len(text)
    if state == 0:
        match_commands = []
        for w in all_commands:
            if text == w[:n]:
                match_commands += [w]
    if state < len(match_commands):
        return match_commands[state]
    return None


def main():
    global yes
    global noauth
    global backup

    # remove commas and insert the arguments appropriately
    oldargv = sys.argv
    sys.argv = oldargv[0:2]
    for i in range(2, len(oldargv)):
        sys.argv += oldargv[i].split(",")

    description = ("wajig is a simple and unified package management front-end "
                   "for Debian and its derivatives.")
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
    backup = result.backup
    util.fast = result.fast
    if result.dist:
        util.dist = result.dist
    util.recommends_flag = result.recommends
    util.recommends_flag = result.norecommends
    args = result.args
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
    select_command(command, args, result.verbose)


def select_command(command, args, verbose):
    "Select the appropriate command and execute it."

    global yes

    if command in ["addcdrom", "cdromadd"]:
        commands.addcdrom(command, args)

    elif command == "addrepo":
        commands.addrepo(command, args)

    elif command in ["autoalts", "autoalternatives"]:
        commands.autoalts(command, args)

    elif command == "autodownload":
        commands.autodownload(args, verbose)

    elif command == "autoclean":
        commands.autoclean(args)

    elif command == "autoremove":
        commands.autoremove(args)

    elif command == "reportbug":
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
        commands.upgrade(args, yes, noauth)

    elif command == "distupgrade":
        commands.distupgrade(args, yes, noauth)

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

    elif command in ["findpkg", "unofficial"]:
        if util.requires_one_arg(command, args, "one package name") \
        and util.requires_package("wget", "/usr/bin/wget"):
            commands.do_findpkg(args[1])

    elif command == "fixconfigure":
        if util.requires_no_args(command, args):
            perform.execute("dpkg --configure --pending",
                             root=True)

    elif command == "fixinstall":
        if util.requires_no_args(command, args):
            perform.execute("apt-get --fix-broken {0} install".format(noauth),
                             root=True)

    elif command == "fixmissing":
        if util.requires_no_args(command, args):
            perform.execute("apt-get --fix-missing {0} upgrade".format(noauth),
                             root=True)

    elif command == "force":
        if util.requires_args(command, args, "a package name"):
            commands.do_force(args[1:])

    elif command == "help":
        commands.help(args)

    elif command == "hold":
        commands.hold(args)

    elif command == "info":
        if util.requires_one_arg(command, args, "one filename"):
            perform.execute("dpkg --info " + args[1])

    elif command in ["init", "reset"]:
        if util.requires_no_args(command, args):
            changes.reset_files()

    elif command in "install isntall autoinstall".split():
        # Okay, so I'm sometimes dyslexic :-)
        if util.requires_args(command, args, "packages, .deb files, or a url"):
            # kept so as not to break anyone's setup; consider it deprecated;
            # it's not even advertised no more (removed from docs)
            if command == "autoinstall":
                yes = "--yes"
            commands.do_install(args[1:], yes, noauth, util.dist)

    elif command in ["installs", "suggested"]:
        if util.requires_one_arg(command, args, "a single package name"):
            commands.do_install_suggest(args[1], yes, noauth)

    elif args[0].startswith('install') and "/" in args[0]:
        # For example: install/unsable
        util.requires_args(args[0], args,
                          "a list of packages, .deb files, or url")
        dist = args[0].split("/")[1]
        perform.execute("apt-get --target-release {0} install {1}".\
                         format(dist, " ".join(args[1:])),
                         root=True)

    elif command == "integrity":
        if util.requires_no_args(command, args):
            perform.execute("debsums --all --silent")

    elif command == "large":
        commands.do_size(args[1:], 10000)

    elif command == "lastupdate":
        if util.requires_no_args(command, args):
            perform.execute("/bin/ls -l --full-time " +
                            changes.available_file +
                            " 2>/dev/null |awk '{printf \"Last update was " +
                            "%s %s %s\\n\"" +
                            ", $6, $7, $8}' | sed 's|\.000000000||'")

    elif command in ["list", "listwide"]:
        if util.requires_opt_arg(command, args, "string to filter on"):
            cmd = ""
            if command == "listwide":
                cmd += "COLUMNS=200 "
            cmd += "dpkg --list '*' | grep -v 'no description avail'"
            if len(args) > 1:
                cmd += " | egrep '" + args[1] + "' | sort -k 1b,1"
            if command == "listwide":
                cmd += "| sed 's|   *|  |g'"
            perform.execute(cmd)

    elif command == "listall":
        if util.requires_opt_arg(command, args, "string to filter on"):
            cmd = "apt-cache dumpavail |" +\
                            "egrep \"^(Package|Description): \" |" +\
                            "awk '/^Package: /{pkg=$2} /^Description: /" +\
                                 "{printf(\"%-24s %s\\n\", pkg," +\
                                 "substr($0,13))}' |" +\
                            "sort -u -k 1b,1"
            if len(args) == 2:
                cmd = cmd + " | grep '" + args[1] + "'"
            perform.execute(cmd)

    elif command in ["listalts", "listalternatives"]:
        if util.requires_no_args(command, args):
            perform.execute("ls /etc/alternatives/ | " +\
                            "egrep -v '(\.1|\.1\.gz|\.8|\.8\.gz|README)$'")

    elif command == "listcache":
        if util.requires_opt_arg(command, args, "string to filter on"):
            cmd = "printf 'Found %d files %s in the cache.\n\n'\
            $(ls /var/cache/apt/archives/ | wc -l) \
            $(ls -sh /var/cache/apt/archives/ | head -1 | awk '{print $2}')"
            perform.execute(cmd)
            cmd = "ls /var/cache/apt/archives/"
            if len(args) == 2:
                cmd = cmd + " | grep '" + args[1] + "'"
            cmd += "; echo"
            perform.execute(cmd)

    elif command in ["listcommands", "commands"]:
        if util.requires_no_args(command, args):
            documentation.help()

    elif command == "listdaemons":
        if util.requires_no_args(command, args):
            perform.execute("printf 'Found %d daemons in /etc/init.d.\n\n'\
            $(ls /etc/init.d/ | \
            egrep -v '(~$|README|-(old|dist)|\.[0-9]*$)' | wc -l)")
            perform.execute("ls /etc/init.d/ | \
            egrep -v '(~$|README|-(old|dist)|\.[0-9]*$)' |\
            pr --columns=3 --omit-header")

    elif command == "listfiles":
        if util.requires_one_arg(command, args,
                            "the name of a single Debian package or deb file"):
            if re.match(".*\.deb$", args[1]):
                perform.execute("dpkg --contents " + args[1])
            else:
                perform.execute("dpkg --listfiles " + args[1])

    elif command == "listsection":
        if util.requires_one_arg(command, args, "the name of a Debian Section." +
                            "\nUse the LIST-SECTIONS command for a list " +
                            "of Debian Sections."):
            commands.do_listsection(args[1])

    elif command == "listsections":
        if util.requires_no_args(command, args):
            commands.do_listsections()

    elif command == "listhold":
        if util.requires_no_args(command, args):
            perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")

    elif command == "listinstalled":
        if util.requires_opt_arg(command, args, "string to filter on"):
            commands.do_listinstalled(args[1:])

    elif command == "listlog":
        perform.execute("cat /var/log/apt/history.log")

    elif command == "listnames":
        if util.requires_opt_arg(command, args, "at most one argument"):
            commands.do_listnames(args[1:])

    elif command == "listscripts":
        if util.requires_one_arg(command, args, "a package name or deb file"):
            commands.do_listscripts(args[1])

    elif command == "liststatus":
        if util.requires_opt_arg(command, args, "package name"):
            cmd = "COLUMNS=400 "
            cmd += "dpkg --list '*' | grep -v 'no description avail'"
            cmd += " | awk '{print $1,$2}'"
            if len(args) > 1:
                cmd += " | egrep '" + args[1] + "' | sort -k 1b,1"
            perform.execute(cmd)

    elif command == "localdistupgrade":
        if util.requires_no_args(command, args):
            perform.execute("apt-get --no-download --ignore-missing " +
                            "--show-upgraded dist-upgrade",
                             root=True)

    elif command == "localupgrade":
        if util.requires_no_args(command, args):
            perform.execute("apt-get --no-download --ignore-missing " + \
                            "--show-upgraded upgrade",
                             root=True)

    elif command == "moo":
        perform.execute("apt-get moo")

    elif command == "madison":
        perform.execute("apt-cache madison " + " ".join(args[1:]))

    elif command == "move":
        if util.requires_no_args(command, args):
            perform.execute("apt-move update",
                             root=True)
            # Then clean out the cached archive.
            perform.execute("apt-get clean",
                             root=True)

    elif command == "new":
        if util.requires_opt_arg(command, args, "whether to INSTALL the new pkgs"):
            if len(args) == 1:
                commands.do_describe_new()
            elif args[1].lower() == "install":
                commands.do_describe_new(install=True)
            else:
                print("NEW only accepts optional argument INSTALL")
                util.finishup(1)

    elif command in ["newupgrades", "newupgrade"]:
        if util.requires_opt_arg(command, args, "whether to INSTALL upgraded pkgs"):
            if len(args) == 1:
                commands.do_newupgrades()
            elif args[1].lower() == "install":
                commands.do_newupgrades(install=True)
            else:
                print("NEWUPGRADES only accepts " + \
                      "optional argument INSTALL")
                util.finishup(1)

    elif command == "nonfree":
        if util.requires_no_args(command, args):
            if util.requires_package("vrms", "/usr/bin/vrms"):
                perform.execute("vrms")

    elif command in ["orphans", "listorphans"]:
        if util.requires_no_args(command, args):
            if util.requires_package("deborphan", "/usr/bin/deborphan"):
                perform.execute("deborphan")

    elif command in ["policy", "available"]:
        perform.execute("apt-cache policy " + " ".join(args[1:]))

    elif command in ["purge", "purgedepend"]:
        if util.requires_args(command, args, "a list of packages"):
            perform.execute("apt-get {0} {1} --auto-remove purge {2}".format(\
                             yes, noauth, " ".join(args[1:])),
                             root=True)

    elif command == "purgeorphans":
        # Deborphans does not require root, but dpkg does,
        # so build up the orphans list first, then pass that to dpkg.
        if util.requires_no_args(command, args) \
        and util.requires_package("deborphan", "/usr/bin/deborphan"):
            packages = str()
            for package in perform.execute("deborphan", pipe=True):
                packages += " " + package.strip()
            if packages:
                perform.execute("apt-get purge" + packages,
                                 root=True)

    elif command == "purgeremoved":
        if util.requires_no_args(command, args):
            packages = str()
            cmd = "dpkg-query --show --showformat='${Package}\t${Status}\n' |"\
            + " grep \"deinstall ok config-files\" | cut -f 1 "
            for package in perform.execute(cmd, pipe=True):
                packages += " " + package.strip()
            if packages:
                perform.execute("apt-get purge" + packages,
                                 root=True)

    elif command in ["readme", "news"]:
        if util.requires_one_arg(command, args, "a single package"):
            docpath = "/usr/share/doc/" + args[1] + "/"
            if not os.path.exists(docpath):
                print("No docs found for '{0}'. Is it installed?".format(args[1]))
                return
            if command == "news":
                li = "NEWS.Debian NEWS".split()
            else:
                li = "README README.Debian USAGE".split()
            found = False
            for x in li:
                path = docpath + x
                cat = "cat"
                if not os.path.exists(path):
                    path += ".gz"
                    cat = "zcat"
                if os.path.exists(path):
                    found = True
                    print("{0:=^72}".format(" {0} ".format(x)))
                    sys.stdout.flush()
                    perform.execute(cat + " " + path)
            if not found:
                print("No {0} file found for {1}.".format(command.upper(), args[1]))

    elif command in "listrecommended":
        command = "aptitude search '" + \
                  "?and( ?automatic(?reverse-recommends(?installed)), "+ \
                  "?not(?automatic(?reverse-depends(?installed))) )'"
        perform.execute(command)

    elif command in ["recursive", "recdownload"]:
        if util.requires_args(command, args, "a list of packages"):
            commands.do_recdownload(args[1:])

    elif command == "reconfigure":
        if len(args) > 1:
            perform.execute("dpkg-reconfigure " + " ".join(args[1:]),
                             root=True)
        else:
            perform.execute("gkdebconf",
                             root=True)

    elif command == "reinstall":
        if util.requires_args(command, args, "a list of packages"):
            perform.execute("apt-get install --reinstall {0} {1} {2}".\
                             format(noauth, yes, " ".join(args[1:])),
                             root=True)

    elif command in "reload restart start stop".split():
        if util.requires_one_arg(command, args, "name of service to " + command):
            perform.execute("service {0} {1}".format(args[1], command),
                             root=True)

    elif command in ["remove", "removedepend"]:
        if util.requires_args(command, args, "a list of packages"):
            perform.execute("apt-get {0} {1}--auto-remove remove {2}".format(\
                             yes, noauth, " ".join(args[1:])),
                             root=True)

    elif command == "removeorphans":
        if util.requires_no_args(command, args) \
        and util.requires_package("deborphan", "/usr/bin/deborphan"):
            packages = str()
            for package in perform.execute("deborphan", pipe=True):
                packages += " " + package.strip()
            if packages:
                perform.execute("apt-get remove" + packages, root=True)

    elif command in ["repackage", "package"]:
        if util.requires_one_arg(command, args, "name of an installed package") \
        and util.requires_package("dpkg-repack", "/usr/bin/dpkg-repack") \
        and util.requires_package("fakeroot", "/usr/bin/fakeroot"):
            perform.execute("fakeroot --unknown-is-real dpkg-repack " + args[1],
                             root=False)

    elif command == "rpminstall":
        if util.requires_one_arg(command, args,
        "a Red Hat package file name (.rpm)"):
            perform.execute("alien --install " + args[1],
                             root=True)

    elif command in ["rpmtodeb", "rpm2deb"]:
        if util.requires_one_arg(command, args,
        "a Red Hat package file name (.rpm)"):
            perform.execute("alien " + args[1],
                             root=True)

    elif command == "search":
        if util.requires_args(command, args, "a list of words to search for"):
            perform.execute("apt-cache search " + " ".join(args[1:]))

    elif command == "searchapt":
        util.requires_one_arg(command, args, "one of stable|testing|unstable")
        util.requires_package("netselect-apt", "/usr/bin/netselect-apt")
        perform.execute("netselect-apt " + args[1],
                         root=True)

    elif command == "showdistupgrade":
        if util.requires_no_args(command, args):
            perform.execute("apt-get --show-upgraded --simulate dist-upgrade",
                             root=True)

    elif command == "showinstall":
        if util.requires_args(command, args, "a list of packages"):
            perform.execute("apt-get --show-upgraded --simulate install " + \
                             " ".join(args[1:]),
                             root=True)

    elif command == "showremove":
        if util.requires_args(command, args, "a list of packages"):
            perform.execute("apt-get --show-upgraded --simulate remove " + \
                             " ".join(args[1:]),
                             root=True)

    elif command == "showupgrade":
        if util.requires_no_args(command, args):
            perform.execute("apt-get --show-upgraded --simulate upgrade",
                             root=True)

    elif command in ["size", "sizes"]:
        commands.do_size(args[1:])

    elif command == "snapshot":
        if util.requires_no_args(command, args):
            commands.do_status([], snapshot=True)

    elif command == "source":
        util.requires_args(command, args, "a list of package names")
        util.requires_package("dpkg-source", "/usr/bin/dpkg-source")
        perform.execute("apt-get source " + " ".join(args[1:]))

    elif command == "status":
        commands.do_status(args[1:])

    elif command in ["statusmatch", "statussearch"]:
        if util.requires_one_arg(command, args,
        "a search string for the package name"):
            packages = [s.strip() for s in commands.do_listnames(args[1:], pipe=True).readlines()]
            if len(packages) > 0:
                commands.do_status(packages)
            else:
                print("No packages found matching '{0}'".format(args[1]))
        #
        # Simplest thing to do is call wajig again.  Not the right way
        # but works for now.
        #
        # This was too slow and was not stopping when killed!
        #perform.execute("apt-cache search " \
        #                    + util.concat(args[1:]) \
        #                    + " | awk '{print $1}' " \
        #                    + " | xargs wajig status ")

    elif command == "tasksel":
        util.requires_no_args(command, args)
        util.requires_package("tasksel", "/usr/bin/tasksel")
        perform.execute("tasksel", root=True)

    elif command == "toupgrade":
        if util.requires_no_args(command, args):
            commands.do_toupgrade()

    # edd 03 Sep 2003  unhold patch based on hold semantics
    elif command == "unhold":
        if util.requires_args(command, args,
        "a list of packages to remove from hold"):
            commands.do_unhold(args[1:])
        # TODO Perhaps I can use map to "execute" over each package

    elif command == "update":
        util.requires_no_args(command, args)
        commands.do_update()

    # For testing only!
    elif command == "updateavailable":
        if util.requires_no_args(command, args):
            changes.update_available()

    elif command in "updatealts updatealternatives setalts setalternatives".split():
        if util.requires_one_arg(command, args, "name of alternative to update"):
            perform.execute("update-alternatives --config " + args[1], root=True)

    elif command == "updatepciids":
        if util.requires_package("pciutils", "/usr/bin/update-pciids"):
            if util.requires_no_args(command, args):
                perform.execute("update-pciids",
                                 root=True)

    elif command == "updateusbids":
        if util.requires_package("usbutils", "/usr/sbin/update-usbids") \
        and util.requires_no_args(command, args):
            perform.execute("update-usbids",
                             root=True)

    elif command == "upgradesecurity":
        sources_list = tempfile.mkstemp(".security", "wajig.", "/tmp")[1]
        sources_file = open(sources_list, "w")
        # check dist
        sources_file.write("deb http://security.debian.org/ " +\
                           "testing/updates main contrib non-free\n")
        sources_file.close()
        perform.execute("apt-get --no-list-cleanup --option Dir::Etc::SourceList=" +\
                        "{0} update".format(sources_list),
                        root=True)
        perform.execute("apt-get --option Dir::Etc::SourceList={0} upgrade".\
                         format(sources_list),
                         root=True)
        if os.path.exists(sources_list):
            os.remove(sources_list)

    elif command == "verify":
        if util.requires_one_arg(command, args, "a package name") \
        and util.requires_package("debsums", "/usr/bin/debsums"):
            perform.execute("debsums " + args[1])

    elif command in ["version", "versions"]:
        if command == "version" and len(args) == 1:
            documentation.version()
        elif util.requires_package("apt-show-versions",
                              "/usr/bin/apt-show-versions"):
            commands.versions(args[1:])

    else:
        print("Command not recognised; run 'wajig commands' for a list")


#------------------------------------------------------------------------
#
# Start it all
#
#------------------------------------------------------------------------
if __name__ == '__main__':
    main()
