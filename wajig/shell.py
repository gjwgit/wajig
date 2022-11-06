#!/usr/bin/python3
#
# This file is part of wajig.  The copyright file is at debian/copyright.

import subprocess
import readline
import os
import atexit


HISTFILE = os.path.join(os.environ["HOME"], ".wajig", ".wajig-history")


def main():

    try:
        readline.read_history_file(HISTFILE)
    except IOError:
        pass
    readline.parse_and_bind('tab: complete')

    # 20211030 Start exploring implementation of completer.
    #
    # from thefuzz import process as fuzzyprocess
    # import rlcompleter
    #
    # def completer(text, state):
    #     cmds = ["addcdrom", "addrepo", "aptlog", "autoalts",
    #             "autoclean", "autodownload", "autoremove", "build",
    #             "builddeps", "changelog", "clean", "commands",
    #             "contents", "dailyupgrade", "dependents", "describe",
    #             "describenew", "distupgrade", "download",
    #             "editsources", "extract", "fixconfigure",
    #             "fixinstall", "fixmissing", "force", "hold", "info",
    #             "init", "install", "installsuggested", "integrity",
    #             "large", "lastupdate", "listall", "listalternatives",
    #             "listcache", "listdaemons", "listfiles", "listhold",
    #             "listinstalled", "listlog", "listnames",
    #             "listpackages", "listscripts", "listsection",
    #             "listsections", "liststatus", "localupgrade",
    #             "madison", "move", "new", "newdetail", "news",
    #             "nonfree", "orphans", "passwords", "policy", "purge",
    #             "purgeorphans", "purgeremoved", "rbuilddeps",
    #             "readme", "reboot", "recdownload", "recommended",
    #             "reconfigure", "reinstall", "reload", "remove",
    #             "removeorphans", "repackage", "reportbug", "repos",
    #             "restart", "rmrepo", "rpm2deb", "rpminstall",
    #             "search", "searchapt", "show", "sizes", "snapshot",
    #             "source", "start", "status", "stop", "sysinfo",
    #             "tasksel", "todo", "toupgrade", "tutorial", "unhold",
    #             "unofficial", "update", "updatealternatives",
    #             "updatepciids", "updateusbids", "upgrade",
    #             "upgradesecurity", "verify", "version", "versions",
    #             "whichpackage"]
    #     return(fuzzyprocess.extract(text, cmds)[state][0])

    # readline.set_completer(completer)
   
    while True:
        try:
            command_line = input("wajig> ")
        except EOFError:
            print()
            break
        if command_line in "exit quit bye".split():
            break
        if command_line:
            command = "wajig " + command_line
            subprocess.call(command.split())

    try:
        readline.write_history_file(HISTFILE)
    except IOError:
        pass


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print()
    atexit.register(readline.write_history_file, HISTFILE)
