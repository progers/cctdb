#!/usr/bin/env python

from cct import CCT, Function
import compare
import os
import subprocess
import unittest

class TestIntegration(unittest.TestCase):

    def testBrokenQuicksortExample(self):
        executable = "examples/brokenQuicksort/brokenQuicksort"
        module = os.getcwd() + "/examples/brokenQuicksort/brokenQuicksort"
        function = "sort(int*, int)"

        # Ensure we can list our module.
        command = "./listModules.py " + executable
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual(0, proc.returncode)
        self.assertEqual("", err)
        self.assertNotEqual("", out)
        modules = out.split("\n")
        self.assertIn(module, modules)

        # Ensure we can list our function.
        command = "./listFunctions.py -m '" + module + "' " + executable
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual(0, proc.returncode)
        self.assertEqual("", err)
        self.assertNotEqual("", out)
        functions = out.split("\n")
        self.assertIn(function, functions)

        # Record a good run.
        command = "./record.py -m '" + module + "' -f '" + function + "' " + executable + " 1 6 3 9 0"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual(0, proc.returncode)
        self.assertEqual("", err)
        self.assertNotEqual("", out)
        self.assertTrue(len(out) > 1)
        goodCct = CCT.fromJson(out)
        self.assertEqual(function, goodCct.calls[0].name)
        self.assertEqual("quicksort(int*, int, int)", goodCct.calls[0].calls[0].name)

        # Record a bad run.
        command = "./record.py -m '" + module + "' -f '" + function + "' " + executable + " 1 6 5 9 0"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual(0, proc.returncode)
        self.assertEqual("", err)
        self.assertNotEqual("", out)
        self.assertTrue(len(out) > 1)
        badCct = CCT.fromJson(out)
        self.assertEqual(function, badCct.calls[0].name)
        self.assertEqual("quicksort(int*, int, int)", badCct.calls[0].calls[0].name)

        # Compare the good and bad runs.
        divergences = compare._findDivergences(goodCct, badCct)
        self.assertEqual(len(divergences), 0)
        divergences = compare._findDivergences(badCct, goodCct)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].function.name, "swap(int*, int, int)")
        self.assertEqual(divergences[0].reason, "Equivalent stack was not found.")

if __name__ == "__main__":
    unittest.main()
