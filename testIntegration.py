#!/usr/bin/env python

from cct import CCT, Function
import compare
import os
import subprocess
import unittest

class TestIntegration(unittest.TestCase):

    def testBrokenQuicksortExample(self):
        # Record good and bad runs and save the output to testData/integrationTestOutput{Good,Bad}.json
        command = "lldb --source testData/integrationTestScript.py examples/brokenQuicksort/brokenQuicksort"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual("", err)

        # Compare the two runs.
        command = "./compare.py testData/integrationTestOutputGood.json testData/integrationTestOutputBad.json"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual("", err)
        self.assertEqual("testData/integrationTestOutputBad.json diverged from testData/integrationTestOutputGood.json in 1 places:"
            "\n  swap(int*, int, int) which was called by quicksort(int*, int, int)\n", out)

if __name__ == "__main__":
    unittest.main()
