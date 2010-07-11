# Gnome Glade toolkit utilities
#
# Copyright (c) Graham Williams
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
# Authors: Graham Williams borrowing from gnomeglade.py in meld.

"""Utility classes for working with glade files.

"""
import os
import sys
try:
    import gtk
    import gtk.glade
    import gnome
    import gnome.ui
except ImportError, e:
    print e
    print "Please install python-glade2 and python-gnome2."
    sys.exit(1)
########################################################################
#
# Support
#
def appdir(path):
    return os.path.join(os.path.dirname(sys.argv[0]), path)


class Base:
    """Base class for all glade objects.

    This class handles loading the xml glade file and connects
    all methods named 'on_*' to the signals in the glade file.

    The handle to the xml file is stored in 'self.xml'. The
    toplevel widget is stored in 'self.widget'.

    In addition it calls widget.set_data("pyobject", self) - this
    allows us to get the python object given only the 'raw' gtk+
    object, which is sadly sometimes necessary.
    """

    def __init__(self, file, root):
        """Load the widgets from the node 'root' in file 'file'.

         Automatically connects signal handlers named 'on_*'.
        """
        self.xml = gtk.glade.XML(file, root)
        #
        # Is this now replacable by the locals() as in:
        # self.xml.signal_autoconnect(locals())
        #
        handlers = {}
        for h in filter(lambda x: x.startswith("on_"), dir(self.__class__)):
            handlers[h] = getattr(self, h)
        self.xml.signal_autoconnect(handlers)
        self.widget = getattr(self, root)
        self.widget.set_data("pyobject", self)
        #
        # Handle the widow manger close button.
        #
        self.widget.connect("destroy", self.quit)

    def __getattr__(self, key):
        """Allow glade widgets to be accessed as self.widgetname.
        """
        widget = self.xml.get_widget(key)
        if widget:  # cache lookups
            setattr(self, key, widget)
            return widget
        raise AttributeError(key)

    def flushevents(self):
        """Handle all the events currently in the main queue and return.
        """
        while gtk.events_pending():
            gtk.main_iteration()

    def _map_widgets_into_lists(self, widgetnames):
        """Put sequentially numbered widgets into lists.

        e.g. If an object had widgets self.button0, self.button1, ...,
        then after a call to object._map_widgets_into_lists(['button'])
        object has an attribute self.button == [self.button0,self.button1,...].
        """
        for item in widgetnames:
            setattr(self, item, [])
            list = getattr(self, item)
            i = 0
            while 1:
                key = "%s%i" % (item,i)
                try:
                    val = getattr(self, key)
                except AttributeError:
                    break
                list.append(val)
                i += 1

########################################################################
#
# GnomeGladeComponent
#
class Component(gtk.Widget, Base):
    """A convenience base class for widgets which use glade.
    """

    def __init__(self, file, root):
        """Create from node 'root' in a specified file"""
        Base.__init__(self, file, root)


########################################################################
#
# GnomeGladeApp
#
class GnomeApp(gnome.ui.App, Base):
    """A convenience base class for apps created in glade.
    """

    def __init__(self, name, title, version, file, root=None):
        self.program = gnome.program_init(name, version)
        gnome.ui.App.__init__(self, name, title)
        Base.__init__(self, file, root)
        self.widget.set_title(title)

    def mainloop(self):
        """Enter the gtk main loop.
        """
        gtk.main()

    def quit(*args):
        """Signal the gtk main loop to quit.
        """
        gtk.main_quit()


class Dialog(gtk.Dialog, Base):
    """A convenience base class for dialogs created in glade"""

    def __init__(self, file, root):
        """Create from node 'root' in a specified file"""
        gtk.Dialog.__init__(self)
        Base.__init__(self, file, root)

########################################################################
#
# Own Dialogs
#
# These are independent of Glade!
#
class InfoDialog:

    def __init__(self, parent, message):
        dlg = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                              gtk.MESSAGE_INFO,
                              gtk.BUTTONS_OK,
                              message)
        dlg.run()
        dlg.destroy()


class WarningDialog:

    def __init__(self, parent, message):
        dlg = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                              gtk.MESSAGE_WARNING,
                              gtk.BUTTONS_OK,
                              message)
        dlg.run()
        dlg.destroy()


class ErrorDialog:

    def __init__(self, parent, message):
        dlg = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                              gtk.MESSAGE_ERROR,
                              gtk.BUTTONS_OK,
                              message)
        dlg.run()
        dlg.destroy()


class QuestionDialog:

    def __init__(self, parent, message):
        dlg = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_YES_NO,
                                   message)
        result = dlg.run()
        self.answer = result == gtk.RESPONSE_YES
        dlg.destroy()

    def get_answer(self):
        return self.answer


def load_pixbuf(fname, size=0):
    """Load an image from a file as a pixbuf, with optional resizing.
    """
    image = gtk.Image()
    image.set_from_file(fname)
    image = image.get_pixbuf()
    if size:
        aspect = float(image.get_height()) / image.get_width()
        image = image.scale_simple(size, int(aspect*size), 2)
    return image.get_pixbuf()
