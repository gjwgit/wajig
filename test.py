#!/usr/bin/python3


"""Test some of wajig functionality."""

import unittest
import difflib

from src import perform
from src import util


class Tests(unittest.TestCase):

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

    # ----
    # testing util.py
    # ----
    def test_util_recommends(self):
        self.assertEqual(util.recommends(), "")
        util.recommends_flag = True
        self.assertEqual(util.recommends(), "--install-recommends")
        util.recommends_flag = False
        self.assertEqual(util.recommends(), "--no-install-recommends")

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


if __name__ == '__main__':
    unittest.main()
