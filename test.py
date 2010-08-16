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
    # missing:
    # * wajig_completer()
    # * wajig_listcommands()

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
