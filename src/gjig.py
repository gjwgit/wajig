#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# Gnome JIG - GNOME interface to wajig sys admin tools
#
# Copyright (c) 2004 Graham J Williams
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version. See the file gpl-license.
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
# Style Guide (see http://www.python.org/doc/essays/styleguide.html)
#
#    Use the "_" convention for function/variable naming (e.g., main_window).
#	Consistent with glade naming. No conflict with Class/Module names.
#    Use Python doc strings to comment each method (triple quotes).
#       Refer to http://www.python.org/peps/pep-0257.html
#    Document functions in docstrings, not in comments, so they are available.
#	Automated tools can extract the docstrings, but not the comments.
#    Use same names in Python as for the Glade objects.
#	No need to remember two names for everything.
#    Classes and Modules generally use the CapWords naming style.
#
# Authors: Graham.Williams@togaware.com
#

########################################################################
#
# Libraries
#
import os
import sys
from socket import gethostname
try:
    import gtk
    import gtk.glade
except ImportError, e:
    print e
    print "Please install python-glade2 and python-gnome2."
    sys.exit(1)
from glutil import GnomeApp, WarningDialog, ErrorDialog, appdir
########################################################################
#
# Global Constants
#
import const
#
# Constants for the number of args for a command.
#
NOARGS   = 0
MOSTONE  = 1
ONLYONE  = 2
SOMEARGS = 3
ANYARGS  = 4
########################################################################
#
# JIG Gnome App
#
class JIG(GnomeApp):
    def __init__(self):
        self.host = gethostname()
        GnomeApp.__init__(self,
                          "gjig",
                          "Gnome JIG: " + self.host,
                          const.version,
                          appdir("gjig.glade"),
                          "gjig_app")
        self.pidlist = []
    ####################################################################
    #
    # Command execution
    #
    def execute_command(self, command, strcommand, argcount=NOARGS,
                        message="", interact=True):
        args = self.arguments_entry.get_text()
        argscount = len(filter(None, args.split(" ")))
        #
        # Check argcount requirement.
        #
        if argcount == NOARGS and argscount > 0 and self.warnings_menu.active:
            WarningDialog(self, "The " + strcommand
                          + " command requires no arguments but " 
                          + str(argscount) + " were found. "
                          + "The arguments will be ignored.")
        if argcount == ONLYONE and argscount != 1:
            ErrorDialog(self, "The " + strcommand
                        + " command requires " + message + ". "
                        + "Please enter the argument in the Package(s): "
                        + "text box.")
            return
        if argcount == MOSTONE and argscount > 1:
            ErrorDialog(self, "The " + strcommand
                        + " command requires " + message + ". "
                        + "Please ensure only a single argument (at most) "
                        + "is entered in the Pacakge(s): text box.")
            return
        if argcount == SOMEARGS and argscount == 0:
            ErrorDialog(self, "The " + strcommand
                        + " command requires " + message + ". "
                        + "Please enter the arguments in the "
                        + "Package(s): text box.")
            return
        #
        # Ignore the arguments if argcount is meant to be NOARGS
        #
        if argcount == NOARGS:
            args = ""
        #
        # Add EDITOR in case its not in the environment.
        # This is for the SOURCES command.
        #
        d = os.environ.copy()
        if not 'EDITOR' in d:
            d['EDITOR'] = '/usr/bin/editor'
        #
        # Build the command to run (in spawn format)
        #
        wajig_command = command + ' ' + args
        # print interact
        if interact == None:
            os.spawnve(os.P_NOWAIT,
                       '/usr/bin/wajig',
                       ['wajig'] + wajig_command.split(), d)
        elif interact:
            wajig_command = 'wajig -p ' + wajig_command
            xterm_command = ('gnome-terminal', '--hide-menubar',
                             '--title=Gnome JIG Executor @ ' +\
                             self.host + ': ' + command +\
                             ' ' + args,
                             '-e', wajig_command)
            newpid = os.spawnve(os.P_NOWAIT,
                                '/usr/bin/gnome-terminal',
                                xterm_command, d)
            self.pidlist += [newpid]
        else:
            viewerxml = gtk.glade.XML(appdir("gjig.glade"), "viewer")
            viewer = viewerxml.get_widget("viewer")
            viewer.set_title('Gnome JIG Viewer @ ' + self.host + ': ' +\
                             wajig_command)
            viewer.show()
            #
            # Set font
            #
            textviewer = viewerxml.get_widget("textviewer")
            import pango
            fontdesc = pango.FontDescription("monospace, 10")
            textviewer.modify_font(fontdesc)
            #
            # Deal with the Close button
            #
            closer = viewerxml.get_widget("viewer_close_button")
            closer.connect("clicked", (lambda self: viewer.destroy()))
            #
            # Set cursor to busy.
            #
            watch = gtk.gdk.Cursor(gtk.gdk.WATCH)
            self.widget.window.set_cursor(watch)
            # Get the actual text window
            child_win = textviewer.get_window(gtk.TEXT_WINDOW_TEXT)
            child_win.set_cursor(watch)
            gtk.gdk.flush()
            #
            # Read results from wajig command
            #
            wajig_command = 'wajig ' + wajig_command
            result = "".join(os.popen(wajig_command).readlines())
            textviewer.get_buffer().set_text(result)
            #
            # Set cursor back to normal
            #
            self.widget.window.set_cursor(None)
            child_win.set_cursor(None)

    ####################################################################
    #
    # Callbacks
    #
    # Menu Items
    #
    def on_about_activate(self, *extra):
        about = gtk.AboutDialog()
        logo = gtk.gdk.pixbuf_new_from_file("/usr/share/wajig/jigsaw-logo.png")

        info = {
            "program-name" : "GNOME JIG",
            "version" : const.version,
            "comments" : "GUI Interface for Debian administration",
            "website" : "http://code.google.com/p/wajig",
            "website-label" : "JIG website",
            "authors" : ["Graham J. Williams <graham@togaware.com>",
                         "Tshepang Lekhonkhobe <tshepang@gmail.com>"],
            "copyright" : "Copyright © 2004-2010 JIG authors",
            "logo" : logo
        }

        for prop, val in info.items():
            about.set_property(prop, val)
        about.run()
        about.destroy()

    def on_quit_activate(self, *extra):
        self.cleanup()
        self.quit()
    #
    # Build a dictionary of the commands
    #
    # "command" : (Description, Arg Count, Interactive, Message)
    #
    # The Interactive flag must be True for any applications requiring
    # a password (i.e., any sudo interactions) or confirmations.
    # Use None if no window is required, since the application will start
    # up its own window.
    #
    clicked = {
        "auto_clean" : ("Auto Clean", NOARGS, True, ""),
        "auto_download" : ("Auto Download", NOARGS, True, ""),
        "policy" : ("Available", SOMEARGS, False, "a list of packages"),
        "bug" : ("Bug", ONLYONE, True, "a single named package"),
        "changelog" : ("Change Log", SOMEARGS, False, "a list of packages"),
        "clean" : ("Clean", NOARGS, True, ""),
        "dependents" : ("Dependents", ONLYONE, False, "a single named package"),
        "describe" : ("Describe", SOMEARGS, False, "a list of packages"),
        "detail" : ("Detail", SOMEARGS, False, "a list of packages"),
        "detail_new" : ("Detail New", NOARGS, False, ""),
        "dist_upgrade" : ("Dist Upgrade", NOARGS, True,  ""),
        "fix_configure" : ("Fix Configure", NOARGS, True, ""),
        "fix_install" : ("Fix Install", NOARGS, True, ""),
        "fix_missing" : ("Fix Missing", NOARGS, True, ""),
        "force" : ("Force", SOMEARGS, True, "a list of packages"),
        "hold" : ("Hold", SOMEARGS, False, "a list of packages"),
        "install" : ("Install", SOMEARGS, True, "a list of packages/.deb/url"),
        "installs" : ("Install+S",SOMEARGS,True,"a list of packages/.deb/url"),
        "large" : ("Large", NOARGS, False, ""),
        "last_update" : ("Last Update", NOARGS, False, ""),
        "list" : ("List", MOSTONE, False, "at most one argument"),
        "list_alts" : ("List Alts", NOARGS, False, ""),
        "list_daemons" : ("List Daemons", NOARGS, False, ""),
        "list_files" : ("List Files", ONLYONE, False, "a single package name"),
        "list_hold" : ("List Hold", NOARGS, False, ""),
        "list_names" : ("List Names", MOSTONE, False, "at most one argument"),
        "local_upgrade" : ("Local Upgrade", NOARGS, True, ""),
        "new" : ("New", NOARGS, False, ""),
        "new_upgrades" : ("New Upgrades", NOARGS, False, ""),
        "news" : ("News", SOMEARGS, False, "a list of packages"),
        "nonfree" : ("Non Free", NOARGS, False, ""),
        "orphans" : ("Orphans", NOARGS, False, ""),
        "purge" : ("Purge", SOMEARGS, True, "a list of packages"),
        "purge_orphans" : ("Purge Orphans", NOARGS, True, ""),
        "rec_download" : ("Rec Download", SOMEARGS, True,"a list of packages"),
        "reconfigure" : ("Reconfigure", MOSTONE, True, "at most one package"),
        "remove" : ("Remove", SOMEARGS, True, "a list of packages"),
        "repackage" : ("Repackage", ONLYONE, True, "a single package name"),
        "show_install" : ("Show Install", SOMEARGS,False,"a list of packages"),
        "show_remove" : ("Show Remove", SOMEARGS, False, "a list of packages"),
        "show_upgrade" : ("Show Upgrade", NOARGS, False, ""),
        "sizes" : ("Sizes", NOARGS, False, ""),
        "start" : ("Start Daemon", ONLYONE, False, "a single daemon"),
        "status" : ("Status", SOMEARGS, False, "a list of packages"),
        "stop" : ("Stop Daemon", ONLYONE, False, "a single daemon"),
        "to_upgrade" : ("To Upgrade", NOARGS, False, ""),
        "unhold" : ("UnHold", SOMEARGS, False, "a list of packages"),
        "unofficial" : ("Unofficial",ONLYONE,False,"a string or package name"),
        "update" : ("Update", NOARGS, True, ""),
        "update_alts" : ("Update Alts", ONLYONE, True, "a single alternative"),
        "upgrade" : ("Upgrade", NOARGS, True,  ""),
        "whichpkg" : ("Which Pkg", ONLYONE, False, "a string or path"),
        }
    #
    # Define the callbacks for each command
    #
    for i in clicked:
        fndef = """def on_%s_button_clicked(self, *extra):
            self.execute_command('%s','%s',%i,'%s',%s )""" % \
            (i, i, clicked[i][0], clicked[i][1], clicked[i][3], clicked[i][2])
        exec fndef
    #
    # Other GUI Functionality
    #
    def on_edit_sources_activate(self, *extra):
        self.execute_command("setup", "Edit Sources", NOARGS, "")
    def on_help_activate(self, *extra):
        self.execute_command("doc", "Docs", interact=False)
    def on_introduction_activate(self, *extra):
        self.execute_command("help", "Introduction", interact=False)
    def on_commands_activate(self, *extra):
        self.execute_command("listcommands", "List Commands", interact=False)
    def on_clear_button_clicked(self, *extra):
        self.arguments_entry.set_text("")
    #
    # Perform actions
    #
    def on_execute_button_clicked(self, *extra):
        command = self.command_entry.get_text()
        self.execute_command(command, command, ANYARGS, "")
    #
    # Quit
    #
    def cleanup(self):
        # Kill each term that has been spawned.
        # Not working for gnome-terminal.
        # Perhaps we don't want to anyhow?
        for i in self.pidlist:
            pass
            #print "Kill " + str(i)
            # Have to kill the wajig instead of the terminal?
            # THIS IS DANGEROUS - FIX IT - FIND FIRST CHILD PROCESS
            #os.kill(i, 15)
    def on_quit_activate(self, *extra):
        self.quit()
    def on_quit_button_clicked(self, *extra):
        self.quit()
    def quit(self, *extra):
        self.cleanup()
        GnomeApp.quit(self)

########################################################################
#
# Main
#
def main():
    JIG().mainloop()
if __name__ == "__main__":
    main()
