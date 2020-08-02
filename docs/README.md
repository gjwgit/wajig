# Wajig: Ubuntu System Administration

Wajig is a simplified, all-in-one-place, system support tool for
Debian and Ubuntu.  It aims to cover every common (and some not so
common) tasks you may need to perform in managing your computer. A few
simple examples:

```console
$ wajig install emacs

$ wajig update
$ wajig distupgrade

$ wajig sysinfo
```

Wajig was implemented by Graham Williams. It has been supported by
Dirk Eddelbuettel and Tshepang Lekhonkhobe, with Tshepang maintaining
and improving wajig for a few years. Contributions also come from
users of wajig, with a special thanks to Reuben Thomas for his many
suggestions and contributions. Graham has resumed maintenance and
development.

Installing
----------

Wajig is available in the Debian and Ubuntu repositories. On Ubuntu,
where sudo is set up by default

```consoles
$ sudo apt install wajig
```

It is also available on [PyPI](https://pypi.org/project/wajig/) from
where it can be installed with:

```console
$ pip3 install wajig
```

If sudo is not set up (see instructions below) then as root:

```console
# apt-get install wajig
```

Resources
---------

* [Home](https://wajig.togaware.com) of wajig.
* [Support Wajig](https://togaware.com/gnulinux/) with a donation.
* [GitHub](https://github.com/gjwgit/wajig) for the source code.
* [Ubuntu](https://packages.ubuntu.com/wajig) for the package entry.
* [PyPI](https://pypi.org/project/wajig/) for the public distribution channel.

Guides
------

* [Read The Docs](https://wajig.readthedocs.io/en/latest/) on line.
* [Togaware](https://togaware.com/linux/survivor/wajig.html) for the
  GNU/Linux Survival Guide.
* [LinOxide
  2019](https://linoxide.com/tools/wajig-package-management-debian/) review.
* [Unix Folk
  2017](https://www.unixmen.com/wajig-alternative-apt-package-manager/) review.
* [Source Digit
  2015](https://sourcedigit.com/16708-install-wajig-alternative-to-apt-package-manager-on-linux-ubuntu-15-04/) review.
* [Link Sprite
  2014](https://learn.linksprite.com/pcduino/linux-applications/wajig-simplyfying-ubuntu-debian-administration/) review.

The Name
--------

The word 'jig' has a couple of meanings, as WordNet and Webster's 1913
Dictionary will confirm. It is a small machine or handy tool used to
guide other tools. It is also a quick dance, generally an old rustic
dance involving kicking and leaping, as well as a light, humorous
piece of writing, especially in rhyme, a farce in verse, or a ballad.
"A jig shall be clapped at, and every rhyme praised and applauded."

The 'wa' in 'wajig' is Japanese, indicating 'harmony' and 'team spirit
and unity'.

History
-------

Development of wajig has been sponsored sponsored and supported by
Togaware Pty Ltd, supporting open source software since the 1980's.

Written in Python, wajig uses traditional Debian/Ubuntu administration
and user tools including apt-get, aptitude, dpkg, apt-cache, and very
many others.

Wajig has evolved over more than 20 years and was rewritten from its
original shell script to be a fully fledged Python program. Its goal
is to support general users and administrators alike in using and
maintaining Debian and Ubuntu based systems.  Thus, it captures in a
single command line tool many common tasks for managing a GNU/Linux
system. It is a single and more comprehensive alternative to an
otherwise large suite of separate tools, starting with apt-get and
apt.

Philosophy
----------

In essence, wajig is simply a front-end to many other commands and
below we demonstrate how to manage your system with wajig.  wajig may
not be the answer you are looking for and that is fine. Wherever a
procedure is illustrated with wajig we will often indicate the
underlying commands that are being used to effect the wajig command.
You can then use these underlying commands directly if you
prefer. 

Indeed, wajig itself will show the commands that it runs if you
provide the --teach or --noop options after the wajig command. Both
will show the command being run, with the latter then not actually
running the command:

```console
$ wajig update --noop
/usr/bin/sudo apt update

$ wajig update --teach
/usr/bin/sudo apt update
[sudo] password for kayon: 
Hit:1 https://brave-browser-apt-release.s3.brave.com stable InRelease
[...]
```

Sometimes the underlying commands can be complex and quite long.

Online information about wajig is at https://wajig.togaware.com.
wajig is hosted on github at https://github.com/gjwgit/wajig. Stack
Overflow (https://stackoverflow.com/) is monitored for questions
relating to wajig so please post your queries there.


Motivation
----------

If you've tried to remember all the different commands to get
different information about different aspects of Debian/Ubuntu package
management and then used other commands to install and remove packages
then you'll know that it can become a little too much.

Swapping between dselect, aptitude, apt-get, dpkg, apt-cache, apt, and
so on is interesting but cumbersome.  Also, dselect and aptitude can
be confusing and even though you can spend hours understanding each of
them, it may not be time particularly well spent.

This Python script simply collects together shortcuts to various
commands!  Clearly no everything is covered, but as new capabilities
are understood they get added to the toolkit.


Basics
------

Wajig is designed to run in such a way as to suit the system it is
running on and the policies of the system administrators.  It can be
run as a normal user, but once a privileged command is required it
will use either su and ask for the root user's password, or else it
can use sudo and rely on the normal user's password. It can also be
run directly as root without any extra setup (i.e., without the need
for sudo or regularly supplying passwords). Using sudo requires a
little setting (see below).

Try the help command for a list of common commands provided by
wajig:
```console
$ wajig help
```

Examples commands include:
```console
$ wajig update               (= apt-get update)
$ wajig install less         (= apt-get install less)
$ wajig new                  (list new packages since last update)
$ wajig newupgrades          (list packages upgraded since last update)
$ wajig updatealts editor    (update the default "editor")
$ wajig restart apache       (restart the apache daemon)
$ wajig listfiles less       (list the files supplied by the "less" pkg)
$ wajig whichpkg stdio.h     (what package supplies this header file)
$ wajig whatis rats          (one line description of the package "rats")
$ wajig orphans              (list libraries not required by other pkgs)
```

For a complete list of available commands:
```console
$ wajig list-commands
```

In most cases, wajig expects a command and will call upon other Debian
tools to perform the command.


Getting Started With Sudo
-------------------------

The aim of wajig is to operate as much as possible as a user command
and to do super user privileged commands only when necessary (if that
is how the system administrator wishes to allow a user to maintain
their system).  The easiest way to do this is to use the sudo package
which will ask you for your password and then run the command as the
super user. If you don't have sudo installed then wajig will use su to
run as super user, but you will need to enter the super user password
frequently. If sudo is installed but not set up for you to access the
appropriate apt-get commands you will see a permission denied message.

In order to allow your user to use sudo, run this command as root:

```console
# adduser <username> sudo
```

The change will take effect after logging out and in again.


Hacking
-------

* Setup::
```console
$ wajig install devscripts debhelper
$ debcheckout wajig
$ cd wajig
```
* Build::
```console
$ debuild -us -uc
```
* Install::
```console
$ sudo debi
```

* Ensure that user-visible changes are mentioned in
  ``debian/changelog``; use ``/usr/bin/debchange`` from within the
  project root directory and do your changes there.

HowTo Release
-------------

* Ensure that the version string in ``src/wajig.py`` as updated from
  the Makefil matches that of latest changelog.

* Ensure that debuild does not emit any lintian errors/warnings.

Available Packages
------------------

The Debian packaging system relies on your local system having some
idea of what packages are available. This is initialised when you
install your system.  You will generally need to update this list of
packages with what is currently available from the Debian archives for
downloading.  If you are staying with the stable release you generally
only need to update the list of available packages once.  The
following command is used to update the information about what is
available for downloading:

```console
$ wajig update                (apt update)
```

(In brackets after the wajig command is the underlying command that
wajig calls upon to perform the operation.)

This uses entries in the file /etc/apt/sources.list to know where to
get the list of available packages from and which release of Debian
you wish to follow.  You can edit this file with:

  $ wajig editsources           (<configured editor> /etc/apt/sources.list)

It will check if $VISUAL and $EDITOR are defined, and use the editors
defined there. If not, it will simply use /usr/bin/sensible-editor.

You need to understand the format of the file /etc/apt/sources.list as
explained in the manual page:

  $ man sources.list

It is pretty straightforward and we will see examples in the next
section.

If you have a Debian CD-ROM or DVD-ROM then you can tell apt what is
available on it using:

  $ wajig addcdrom

To add a Launchpad PPA (Personal Package Archive) repository (used by
Ubuntu) the ADD-REPO command can be used. For example, to add the
daily builds of Google's Chromium browser, do the following:

  $ wajig addrepo ppa:chromium-daily

If you want to check when you last did an update then:

  $ wajig lastupdate

There are quite a few archives available and you can test for a good
connection to one with:

  $ wajig searchapt

This will write a candidate sources.list in the current directory,
which you can then review and add to the system sources.list, if you
wish, with

  $ wajig editsources


FINDING PACKAGES

To search for a particular packages, use:

  $ wajig search                        (apt-cache --names-only)

This will only match a particular string with package names. If you want
a more comprehensive search, one that also searches for package
descriptions, use the "-v|--verbose" options.

To display the list of newly-available packages (after a cache update), use:

  $ wajig new

Note that after the first time you use update all packages will be
considered new! But after the next update the new packages are those
that were not in the available list from the previous update.

Some (and often many) of the packages that you already have installed
on your Debian system may have been upgraded in the archive since the
last time you performed an update. The following command will list
these packages:

  $ wajig newupgrades

For a complete list of the packages you have installed but for which
there are newer versions available on the archive use:

  $ wajig toupgrade

To check the version of any installed package and also the version
available from the archive previously (i.e., the last time, but one,
you performed an upgrade) and now (based on the last time you
performed an update), and to also see the so called Desired and Status
flags of the package, use:

  $ wajig status <package names>        (similar to dpkg -l)

Without a list of package names all installed packages will be listed.

A variation is to list the status of all packages with a given string
in their name:

  $ wajig statussearch <string>

To check for a particular package for which you might guess at part of
its name you can use:

  $ wajig listnames <string>            (apt-cache pkgnames)

Without the string argument all known package names will be listed.

To list the names and current install status of all installed packages
then use:

  $ wajig list

You can also list just the names of the packages installed with:

  $ wajig list-installed

And if you are looking for a particular installed package with a name
containing a particular string then use:

  $ wajig list-installed <string>

To generate a list of packages, with version numbers, which you might
save to file, and then restore a system to just this list of packages
at a later stage, use:

  $ wajig snapshot > snapshop-12dec04

Each package installs some collection of files in different places on
your system (e.g., in /usr/bin/, /usr/man/man1/ and
usr/doc/). Sometimes you like to see where those files go or
even just view the list of files installed. The command to use is:

  $ wajig listfiles <package name>      (dpkg --listfiles )


To list a one-line description for a package use:

  $ wajig whatis <package name>

And to find which package supplies a given file use:

  $ wajig whichpkg <command or file path>

and for a command (e.g., most):

  $ wajig whichpkg $(which -p most)


For unofficial packages (i.e., you came across a package but it doesn't
seem to be in Debian yet) search for a site with:

  $ wajig searchpkg <package-name>


The more detailed description of a package is available with:

  $ wajig detail <package-name>

Here, the package name can be replaced with a specific deb file.

The Debian changelog can be retrieved with:

  $ wajig changelog <package name>

This command only displays changelog entries for upgradable packages.
If you want to display the entire changelog, use:

  $ wajig changelog --verbose <package name>

It may be more practical to run the output through a pager:

  $ wajig changelog --verbose <package name> | pager



INSTALLING PACKAGES

To install a new package (or even to update an already installed
package) all you need do is:

  $ wajig install <package name>        (apt-get install)

(Instead of install you could equivalently say update.)

You can list multiple packages to install with the one command.

The install command will also accept a .deb file.  So, for example, if
you have downloaded a Debian package file (with the .deb extension)
you can install it with:

  $ wajig install <.deb file>           (dpkg -i)

The .deb file will be searched for in both the current directory and
in the apt archive at /var/cache/apt/archive/.

You can list multiple .deb files to install.

If the .deb package file you wish to install is available on the
internet you can give its address and wajig will download then install
it:

  $ wajig install http://samfundet.no/debian/dists/woody/css/xine-dvd-css.deb

Sometimes you may want to install many packages by listing them in a
file, one per line.  You can do this with:

  $ wajig install --fileinput <filename>

The file of packages to install can conveniently be created from the
list of installed packages on another system with:

  $ wajig listinstalled > <filename>    (dpkg --get-selections)


UPGRADING PACKAGES

You can upgrade all installed packages with:

  $ wajig upgrade                       (apt-get -u upgrade)

And you can upgrade all installed packages, remove those packages that
need to be removed (for various reasons, including issues to do with
dependencies) and install all newly required packages in the
distribution with:

  $ wajig distupgrade                  (apt-get -u dist-upgrade)

Note that a dist-upgrade will potentially remove packages where
dependency checking indicates this is necessary. Important packages
(determined by the Priority specification which can be found using the
details command) will be upgraded even at the cost of downgrading
other (less important) packages.

If this is an issue for you then you should use the upgrade command
rather than dist-upgrade. This command will never remove or downgrade
a package.

To upgrade to a specific distribution (e.g., experimental) you can use:

  # wajig distupgrade --dist experimental

Note that the mentioned distribution must also be mentioned in your
/etc/apt/sources.list file.


A neat trick with wajig is the ability to upgrade a collection of
packages all with the same version number to another common version
number:

  $ wajig status | grep 3.2.3-2 | grep 3.3.0-1 | cut -f1 > list
  $ wajig installfile list


REMOVING PACKAGES

Once a package is installed you can remove it with:

  $ wajig remove <package name>         (apt-get remove)

Once again, you can list multiple packages to remove with the one
command.

A remove will not remove configuration files (in case you have done
some configuration of the package and later re-install the package).
To get rid of the configuation files as well use:

  $ wajig purge <package name>          (apt-get --purge remove)


DISPLAYING APT LOG

Whenever a package is installed, removed, upgraded, or downgraded
with either apt, aptitude, or synaptic, a log found at
/var/log/apt/history.log is updated. To display it, run:

  $ wajig list-log                      (cat /var/log/apt/history.log)



CHECKING WHAT'S CHANGED BEFORE INSTALLING

When you install an updated package it is sometimes useful to know
what's changed.  The apt-listchanges package provides a mechanism
whereby when updating packages you will be given a chance to review
the changelog of the package and then decide whether to continue with
the upgrade. Simply install the apt-listchanges package to turn this
feature on.


INSTALLING ALIEN (RedHat/Fedora/CentOS) PACKAGES

RedHat has quite an installed base of users. Some packages
(particularly commercial packages) are available as RedHat packages
(with the rpm extension). These can usually be installed in Debian
with little effort.  The alien package is required to convert the rpm
into deb format which can then be installed. This is taken care of by
wajig:

  $ wajig rpminstall gmyclient-0.0.91b-1.i386.rpm


PUTTING PACKAGES ON HOLD

Occasionally, and particularly if you are following the unstable
release, some packages are broken for various reasons.  This was the
case with the package cdrecord in unstable.  This package was compiled
with kernel 2.4.n and had some kernel specific issues that were done
differently with kernel 2.2.n. At compile time one or the other
options was chosen (but not both!). Thus the newer binary versions of
cdrecord would not run on a system using kernel 2.2.n. One solution is
to build a Debian package of cdrecord using the wajig build command.
Another is to reinstall an older version that worked and then place
the package on hold with:

  $ wajig hold cdrecord

A wajig upgrade would not try to upgrade this package.


BUILDING PACKAGES

Sometimes the binary distribution of the package is configured or
compiled with options that don't suit you. Or it may be compiled for a
more recent release than that which you are using and does not work
for your release. Normally you would then be left on your own to
retrieve the source of the package, configure and compile it, then
install it into /usr/local/.  This is then outside of the Debian
package management system, which is just fine.  But there are better
solutions. One is to tune a specific source package and build a Debian
package from it. The second is to specify general configuration
options for your system and then rebuild many packages with these
options.


BUILDING PACKAGES FROM SOURCE

You can download the source code for any Debian package from the
Debian archive. You can then modify it and generate your own .deb file
for installation. To download the source of a Debian package you will
need deb-src lines in your /etc/apt/sources.list file, such as the
following:

  deb-src http://ftp.debian.org/debian unstable main contrib non-free

Generally you can add the '-src' to copies of pre-existing 'deb'
lines.

To retrieve and unpack a source Debian package use:

  $ wajig source <package names>                (apt-get source)

Note that you can list several packages and grab all of their sources.

The source command downloads a .tar.gz file and a .dsc file for the
package. The .tar.gz file contains the source code and associated
files. The .dsc file contains test information that is used by the
packaging system. The source command will also extract the contents of
the .tar.gz archive into a subdirectory consisting of the package name
and version.

To go one step further and also configure, compile and generate a
default Debian .deb package from source code (useful if you need to
compile a package for your setup specifically) then use instead:

  $ wajig build <package names>

This conveniently installs the needed build-dependencies for you.

If you need to modify the source in some way and rebuild a package:

 $ wajig update
 $ wajig build ncftp
 $ dpkg-source -x ncftp_3.0.2-3.dsc
 $ cd ncftp-3.0.2
 $ fakeroot dpkg-buildpackage -b -u

Note that for some packages, you will get permission-related build errors.
Replace 'fakeroot' with 'sudo' in such cases.


BUILD ARCHITECTURE-OPTIMISED PACKAGES

The apt-build package, a front-end to apt-get, provides a general
solution to build Debian packages tuned (or optimised) for your
architecture.

  $ wajig install apt-build

You will be asked for some options, and these go into
/etc/apt/apt-build.conf:

  build-dir = /var/cache/apt-build/build
  repository-dir = /var/cache/apt-build/repository
  Olevel = -O2
  march = -march=pentium4
  mcpu = -mcpu=pentium4
  options = " "

The built packages will be placed into
/var/cache/apt-build/repository, an can be accessed with the
standard Debian package tools by adding the following line to the top
of /etc/apt/sources.list (which can be done during the
installation of apt-build:

  deb file:/var/cache/apt-build/repository apt-build main

You will need deb-src entries in your /etc/apt/sources.list file to be
able to obtain the source packages.

Being a front-end to apt-get, your first apt-build command might be to
update the list of known available packages (particularly if you have
just added a deb-src entry to /etc/apt/sources.list), although the
following is equivalent:

  $ wajig update

You can then start building packages:

  $ sudo apt-build install most

You can manage a collection of packages to be recompiled and installed
instead of obtaining the default compiled versions. Create the file
/etc/apt/apt-build.list to contain a list of such packages
and then:

  $ sudo apt-build world

One way to get a full list of installed packages is:

  # dpkg --get-selections | awk '{if ($2 == "install") print $1' \\
    > /etc/apt/apt-build.list

Be sure to edit the list to remove, for example, gcc! Then a:

  $ sudo apt-build world

will recompile and optimise all packages.


PINNING DISTRIBUTIONS

With the Debian packaging system you can specify that your packages
come by default from one distribution but you can override this with
packages from other distributions. The concept is called pinning and
after it is set up you can have, for example, testing as
your default release and then include unstable in
/etc/apt/sources.list and install cdrecord from unstable with:

  # apt-get install cdrecord/unstable

The following /etc/apt/preferences makes apt-get use testing unless it
is overridden, even though there are entries for unstable in
/etc/apt/sources.list:

  Package: *
  Pin: release a=testing
  Pin-Priority: 900

  Package: *
  Pin: release o=Debian
  Pin-Priority: -10


RECONFIGURE PACKAGES

  $ wajig reconfigure debconf           (dpkg-reconfigure  debconf)

An alternative where you can specify a particular front end to use for
the configurator is:

  # dpkg-reconfigure --frontend=dialog debconf


SETTING DEFAULT APPLICATIONS

Debian has a system of alternatives for various commands (or
functionalities).  For example, the editor command could be nano or
nvi, or one of a large number of alternative editors.  You can update
the default for this command with:

  $ wajig updatealts editor             (update-alternatives --config editor)

Another common alternative is x-window-manager. You can get a list of
all alternatives with:

  $ wajig listalts                      (ls /etc/alternatives/)

The information is maintained in the directory /etc/alternatives/.

BUGS

If you find a problem with your system and think it might be a bug, use:

  $ wajig bug                           (reportbug)

This will allow you to view bugs recorded against packages and also
allow you to add a new bug report to the Debian bug reporting system.

Otherwise visit the Debian email lists at http://lists.debian.org/ and
search for the problem there.  The advice one gets here is generally
of high quality.


MANAGING DAEMONS OR SERVICES

In addition to managing the installed packages wajig also allows you
to start, stop, reload, and restart services (which are often provided
by so called daemons---processes that run on your computer in the
background performing various functions on an on-going basis).  The
commands all follow the same pattern:

  $ wajig restart <service name>        (/etc/init.d/<service> restart)

The start and stop commands are obvious.  The restart command
generally performs a stop followed by a start.  The reload command
will ask the daemon to reload its configuration files generally
without stopping the daemon, if this is possible.  The services you
can specifiy here depend on what you have installed.  Common services
include:

  apache Web server
  cron   Regular task scheduler
  exim   Email delivery system
  gdm    The Gnome Windows Display Manager (for logging on)
  ssh    The Secure Shell daemon

Generally, daemons are started at system boot time automatically.


ALTERNATIVE APPLICATIONS

Debian has a mechanism for dealing with applications that provide the
same functionality.  We describe here how this mechanism works and how
you can use it to tune your installation.

If you have more than one variant of emacs installed (e.g., emacs19,
emacs20, and xemacs) then you can configure which one you get by
default with:

  $ wajig updatealts emacs

You will be asked to choose from a list of alternatives.

To specify which window manager to use as the system default:

  $ wajig updatealts x-window-manager

Suppose the window-manager you want to use as the default is not
listed as available. You can install it with:

# update-alternatives --install /usr/bin/x-window-manager \\
                      x-window-manager /usr/bin/mywm PRIORITY

Where PRIORITY is a number higher than the highest existing priority
for the x-window-manager alternative.  You can get a list of
priorities with:

# update-alternatives --display x-window-manager

To remove a Window Manager:

# update-alternatives --remove x-window-manager /usr/bin/mywm


PACKAGE ARCHIVES

Local Cache

When packages are installed from the Debian Archives the corresponding
deb files are stored in /var/cache/apt/archive.  This can become quite
populated with older versions of packages and we can clean out these
older versions with:

  $ wajig autoclean                     (apt-get autoclean)

Warning: It is sometimes useful to have older versions of packages
hanging around if you are tracking the unstable release.  Sometimes
the newer versions of packages are broken and you need to revert to an
older version which may not be available from the Debian archives, but
might be in your local download archive.

If you get short of disk space then you might want to remove all the
downloaded deb files (not just the older versions of downloaded files)
with:

  $ wajig clean                         (apt-get clean)

To remove files immediately after they have been installed edit
/etc/apt/apt.conf:

  // Things that effect the APT dselect method
  DSelect
  {
    Clean "auto";   // always|auto|prompt|never
  ;

Historic Packages

To obtain any package version that might have appeared in the archive
include http://snapshot.debian.net in your package sources list and
the name of the package you are interested in. To update your sources
list run:

  $ wajig editsources

to add the following line:

  deb http://snapshot.debian.net/archive pool sed

Then you can do, for example:

  $ wajig available sed
  $ wajig install sed=4.1.2-1


MAINTAINING A DISTRIBUTION ARCHIVE

Downloaded Debian packages are placed into /var/cache/apt/archive. You
can have the files moved into a local hierarchy that mirrors a
standard Debian distribution hierarchy.  Then you can point the
/etc/apt/sources.list to this local archive by using the file://
format.

To set up a local machine as a local (partial) mirror of the Debian
archive, wajig will use the apt-move package.

Edit /etc/apt-move.conf to set the DIST to match your system (default
is stable):

  DIST=unstable

The wajig command move will then move any packages in your
/var/cache/apt/archives into the Debian mirror being created:

  $ wajig move

You can actually create a complete mirror with:

  # apt-move mirror

These commands place the packages into /mirrors/debian. To make it
available on your web server simply:

  # cd /var/www
  # ln -s /mirrors pub

The file /etc/apt/sources.list can then be updated to point to the new
archive as the first place to check for packages (place this lines
first in the file):

  deb http://athens/pub/debian unstable main contrib non-free


All of this might happen on your server (called athens in this
example) and other machines on your local network can then access the
local archive by adding the above line to /etc/apt/sources.list.

If your server is not the most up to date machine (since you may not
want to run the risk of your server becoming unstable), you can rsync
all packages in /var/cache/apt/archives on other machines to the
server and then run the move command on the server:

  # rsync -vr friend:/var/cache/apt/archives/ /var/cache/apt/archives/
  # ssh friend wajig clean         (apt-get clean)
  # wajig move                     (apt-move update)

In fact, on your server you could use the following Python script
saved to file /root/apt-archive.py to automate this for each of the
hosts on the network:

    #!/usr/bin/env python
    import os

    hosts = ['friend', 'cargo']
    archive = '/var/cache/apt/archives/'

    for h in hosts:
        os.system('rsync -vr %s:%s %s' % (h, archive, archive))
        os.system('ssh %s wajig clean' % h)

    os.system('wajig move')

Then set the script up to run:

  # chmod u+x apt-archive.py

and run it as required:

  # ./apt-archive.py

Depending on how you have ssh set up this may ask for your password
for each connection.  To avoid this, you can use public/private keys
with no passphrase, and then the script could be run automatically
using cron each morning by copying the executable script to
/etc/cron.daily/apt-archive. (Scripts in /etc/cron.daily with a py
extension are not run, so be sure to rename the file as suggested
here.)

Local Debian Package Cache

To set up a local Debian cache of deb files that you've created or
downloaded separately:

  # mkdir -p /usr/local/cache/dists/local/local/binary-i386
  # cp *.deb /usr/local/cache/dists/local/local/binary-i386
  # cd /usr/local/cache
  # dpkg-scanpackages dists/local/local/binary-i386 /dev/null \\
  $ dists/local/local/binary-i386/Packages

Then add the following line to /etc/apt/sources.list:

  deb file:/usr/local/cache local local


OTHER COMMANDS

These may work their way into wajig.

You can use the apt-get --download-only option of apt-get to download
the files for an install without actually unpacking and setting up the
packages. For example:

  # wajig update
  # apt-get --download-only dist-upgrade

In this way you are able to leave the download unattended and when you
are ready you can monitor the unpacking and setup.

If things go wrong somewhere then apt may be able to help:

  # apt-get --fix-broken dist-upgrade

but if things still don't work, you may need to use dpkg directly to
remove and isntall packages.

Synchronising Two Installations

The package system maintains a list of all packages installed (and
de-installed). You can access this list, save it to a file, and use it
to mark those same packages for installation (or deinstallation) on
anther machine:

# dpkg --get-selections > dpkg-selections
# dpkg --set-selections < dpkg-selections
# apt-get dselect-upgrade
