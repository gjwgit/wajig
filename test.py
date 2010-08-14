import unittest
from src import perform


class WaJIGTests(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()
