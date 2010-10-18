"""
Test some of WaJIG functionality.

TODO:
* changes.py
* commands.py
* glutil.py
"""

import unittest
import os
import difflib

from src import perform
from src import util


class WaJIGTests(unittest.TestCase):

    # ----
    # testing perform.py
    # ----
    def test_perform_normal(self):
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "set -o noglob; TEST")

    def test_perform_root(self):
        res = perform.execute("TEST", test=True, root=True)
        self.assertEqual(res, "set -o noglob; /usr/bin/sudo TEST")

    def test_perform_langC(self):
        res = perform.execute("TEST", test=True, langC=True)
        self.assertEqual(res, "LC_ALL=C; export LC_ALL; set -o noglob; TEST")

    def test_perform_simulate(self):
        perform.set_simulate(True)
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "TEST")
        perform.set_simulate(False)

    def test_perform_teaching(self):
        perform.set_teaching()
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "Performing: TEST")

    def test_perform_quiet(self):
        perform.set_quiet()
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "set -o noglob; TEST> /dev/null")
        perform.set_quiet(False)

    # ----
    # testing util.py
    # ----
    def test_util_requires_args(self):
        res = util.requires_args("", [1])
        self.assertFalse(res)
        res = util.requires_args("", [1, 2])
        self.assertTrue(res)

    def test_util_requires_no_args(self):
        res = util.requires_no_args("", [1], test=True)
        self.assertTrue(res)
        res = util.requires_no_args("", [1, 2], test=True)
        self.assertFalse(res)

    def test_util_requires_opt_arg(self):
        res = util.requires_opt_arg("", [1, 2])
        self.assertTrue(res)
        res = util.requires_opt_arg("", [1, 2, 3])
        self.assertFalse(res)

    def test_util_requires_one_arg(self):
        res = util.requires_one_arg("", [1])
        self.assertFalse(res)
        res = util.requires_one_arg("", [1, 2])
        self.assertTrue(res)
        res = util.requires_one_arg("", [1, 2, 3])
        self.assertFalse(res)

    def test_util_requires_two_args(self):
        res = util.requires_two_args("", [1, 2])
        self.assertFalse(res)
        res = util.requires_two_args("", [1, 2, 3])
        self.assertTrue(res)
        res = util.requires_two_args("", [1, 2, 3, 4])
        self.assertFalse(res)

    def test_util_requires_package(self):
        res = util.requires_package("ls", "/bin/ls", test=True)
        self.assertTrue(res)
        res = util.requires_package("ls", "TEST", test=True)
        self.assertFalse(res)

    def test_util_package_exists(self):
        self.assertTrue(util.package_exists("dpkg", test=True))
        self.assertFalse(util.package_exists("pkg_does_not_exist", test=True))

    def test_util_upgradable(self):
        # needs root access to APT cache, so ignoring
        pass

    def test_util_concat(self):
        res = util.concat([])
        self.assertEqual(res, "")
        res = util.concat(["TEST1"])
        self.assertEqual(res, "'TEST1' ")
        res = util.concat(["TEST1", "TEST2"])
        self.assertEqual(res, "'TEST1' 'TEST2' ")

    # ----
    # testing bash_completion.py
    # ----
    def test_bash_completion(self):
        bc_ref = """\
have wajig &&
_wajig()
{
    local cur prev opt

    COMPREPLY=()
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    if [ "$COMP_CWORD" -ge "2" ]; then
        COMPREPLY=($( compgen -W "$(apt-cache pkgnames "$cur")" -- $cur ) )
    elif [[ "$cur" == -* ]]; then
        COMPREPLY=($( compgen -W '-b --backup -h --help -n --noauth  \ 
                              -x --pager -p --pause -q --quiet  \ 
                              -s --simulate -t --teaching -v  \ 
                              --verbose -y --yes' -- $cur ) )
    else
        COMPREPLY=($( compgen -W '
        addcdrom addrepo auto-alts auto-clean auto-download bug build \ 
        build-depend changelog clean commands contents daily-upgrade \ 
        dependents describe describe-new detail detail-new dist-upgrade \ 
        docs download download-file editsources extract find-file find-pkg \ 
        fix-configure fix-install fix-missing force help hold init info \ 
        install install-file installs integrity large last-update list \ 
        list-all list-alts list-cache list-commands list-daemons list-files \ 
        list-hold list-installed list-log list-names list-orphans list-scripts \ 
        list-section list-sections list-status list-wide local-dist-upgrade \ 
        local-upgrade madison move new news new-upgrades non-free orphans \ 
        policy purge purge-orphans purge-removed rbuilddeps readme list-recommended \ 
        recursive reconfigure reinstall reload remove remove-file remove-orphans \ 
        repackage reset restart rpm rpminstall search search-apt setup \ 
        showdistupgrade showinstall showremove showupgrade sizes snapshot \ 
        source start status status-search stop tasksel toupgrade unhold \ 
        update update-alts update-pci-ids update-usb-ids upgrade verify \ 
        version versions whatis whichpkg' -- $cur ) )
    fi
}
complete -F _wajig $default wajig""".split("\n")

        wc = "wajig.completion"
        os.system("python bash_completion.py")
        bc_gen = list()

        with open(wc) as f:
            for line in f:
                bc_gen.append(line[:-1])  # remove trailing "\n" char

        if (bc_ref != bc_gen):
            diff = difflib.unified_diff(bc_ref, bc_gen, fromfile="reference", \
                                        tofile="generated", lineterm="")
            for line in diff:
                print line

        self.assertEqual(bc_ref, bc_gen, "Check diff above.")
        if os.path.exists(wc):
            os.unlink(wc)


if __name__ == '__main__':
    unittest.main()
