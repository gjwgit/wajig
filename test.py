"""
Test some of WaJIG functionality.

Not yet done:
* changes.py
* commands.py
* glutil.py
"""

import unittest
from src import perform
from src import wajig


class WaJIGTests(unittest.TestCase):

    # testing perform.py
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
        perform.set_teaching_level(True)
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "Performing: TEST")
        perform.set_teaching_level(False)

    def test_perform_quiet(self):
        perform.set_quiet()
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "set -o noglob; TEST> /dev/null")
        perform.set_quiet(False)

    def test_perform_concat(self):
        res = perform.concat(["TEST1", "TEST2"])
        self.assertEqual(res, "'TEST1' 'TEST2' ")  # me not happy wit' this

    # testing wajig.py
    # missing: wajig_completer()
    def test_wajig_listcommands(self):
        res = wajig.list_commands()
        check = ['addcdrom', 'auto-alts', 'auto-clean', 'auto-download', 'auto-install', 'auto-remove', 'available', 'bug', 'build', 'build-depend', 'changelog', 'clean', 'commands', 'contents', 'daily-upgrade', 'dependents', 'describe', 'describe-new', 'detail', 'detail-new', 'dist-upgrade', 'docs', 'download', 'editsources', 'extract', 'file-download', 'file-install', 'file-remove', 'find-file', 'find-pkg', 'fix-configure', 'fix-install', 'fix-missing', 'force', 'help', 'hold', 'init', 'info', 'install', 'installr', 'installrs', 'installs', 'integrity', 'large', 'last-update', 'list', 'list-all', 'list-alts', 'list-cache', 'list-commands', 'list-daemons', 'list-files', 'list-hold', 'list-installed', 'list-log', 'list-names', 'list-orphans', 'list-scripts', 'list-section', 'list-sections', 'list-status', 'list-wide', 'local-dist-upgrade', 'local-upgrade', 'madison', 'move', 'new', 'news', 'new-upgrades', 'non-free', 'orphans', 'package', 'policy', 'purge', 'purge-depend', 'purge-orphans', 'purge-removed', 'readme', 'recursive', 'recommended', 'reconfigure', 'reinstall', 'reload', 'remove', 'remove-depend', 'remove-orphans', 'repackage', 'reset', 'restart', 'rpminstall', 'rpmtodeb', 'search', 'search-apt', 'setup', 'show', 'showdistupgrade', 'showinstall', 'showremove', 'showupgrade', 'size', 'sizes', 'snapshot', 'source', 'start', 'status', 'status-match', 'status-search', 'stop', 'suggested', 'tasksel', 'toupgrade', 'unhold', 'unofficial', 'update', 'update-alts', 'update-pci-ids', 'update-usb-ids', 'upgrade', 'versions', 'whatis', 'whichpkg']  # is there a better way?
        self.assertEqual(res, check)

    def test_wajig_requires_args(self):
        res = wajig.requires_args("", [1])
        self.assertFalse(res)
        res = wajig.requires_args("", [1, 2])
        self.assertTrue(res)

    def test_wajig_requires_no_args(self):
        res = wajig.requires_no_args("", [1], test=True)
        self.assertTrue(res)
        res = wajig.requires_no_args("", [1, 2], test=True)
        self.assertFalse(res)

    def test_wajig_requires_opt_arg(self):
        res = wajig.requires_opt_arg("", [1, 2])
        self.assertTrue(res)
        res = wajig.requires_opt_arg("", [1, 2, 3])
        self.assertFalse(res)

    def test_wajig_requires_one_arg(self):
        res = wajig.requires_one_arg("", [1])
        self.assertFalse(res)
        res = wajig.requires_one_arg("", [1, 2])
        self.assertTrue(res)
        res = wajig.requires_one_arg("", [1, 2, 3])
        self.assertFalse(res)

    def test_wajig_requires_two_args(self):
        res = wajig.requires_two_args("", [1, 2])
        self.assertFalse(res)
        res = wajig.requires_two_args("", [1, 2, 3])
        self.assertTrue(res)
        res = wajig.requires_two_args("", [1, 2, 3, 4])
        self.assertFalse(res)

    def test_wajig_requires_package(self):
        res = wajig.requires_package("ls", "/bin/ls", test=True)
        self.assertTrue(res)
        res = wajig.requires_package("ls", "TEST", test=True)
        self.assertFalse(res)

if __name__ == '__main__':
    unittest.main()
