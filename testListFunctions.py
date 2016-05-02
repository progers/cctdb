#!/usr/bin/env python

from cct import CCT, Function
import compare
import subprocess
import unittest

class TestListFunctions(unittest.TestCase):

    def testListFunctionsWithBadModule(self):
        command = "./listFunctions.py -m 'ModuleDoesNotExist42' testData/quicksort"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertIn("Could not find module \'ModuleDoesNotExist42\'", err)
        self.assertEqual("", out)

    def testListAllFunctions(self):
        command = "./listFunctions.py testData/quicksort"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        # FIXME(phil): See comment about spurious segfault in lldbRecorder.py
        #self.assertEqual(0, proc.returncode)
        self.assertEqual("", err)
        self.assertNotEqual("", out)
        functions = out.split("\n")
        self.assertIn("sort(int*, int)", functions)
        self.assertIn("swap(int*, int, int)", functions)

if __name__ == "__main__":
    unittest.main()
