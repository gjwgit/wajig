#!/usr/bin/python3


"""Test some of wajig functionality."""

import unittest
import sys

sys.path.append("src")
import perform
import util

import apt

class Tests(unittest.TestCase):

    # ----
    # testing perform.py
    # ----
    def test_perform_normal(self):
        res = perform.execute("TEST", test=True)
        self.assertEqual(res, "TEST")

    def test_perform_root(self):
        res = perform.execute("TEST", test=True, root=True)
        self.assertEqual(res, "/usr/bin/sudo TEST")

    def test_perform_langC(self):
        res = perform.execute("TEST", test=True, langC=True)
        self.assertEqual(res, "LC_ALL=C; export LC_ALL; TEST")

    # ----
    # testing util.py
    # ----
    def test_util_requires_package(self):
        res = util.requires_package("ls", "/bin/ls", test=True)
        self.assertTrue(res)
        res = util.requires_package("ls", "TEST", test=True)
        self.assertFalse(res)

    def test_util_package_exists(self):
        cache = apt.Cache()
        self.assertIsInstance(util.package_exists(cache, "dpkg"),
                              apt.package.Package)
        self.assertFalse(util.package_exists(cache, "no_such", test=True))


if __name__ == '__main__':
    unittest.main()
