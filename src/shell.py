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

    while True:
        command_line = input("wajig> ")
        if command_line in "exit quit bye".split():
            return
        if command_line:
            command = "wajig " + command_line
            subprocess.call(command.split())

if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print()
    atexit.register(readline.write_history_file, HISTFILE)
