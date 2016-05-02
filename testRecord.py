#!/usr/bin/env python

from cct import CCT, Function
import compare
import subprocess
import unittest

# TODO(phil): Add a test of recording a running process.
class TestRecord(unittest.TestCase):

    def testRecordNewProcess(self):
        command = "./record.py -m 'quicksort' -f 'sort(int*, int)' testData/quicksort 1"
        proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        # FIXME(phil): See comment about spurious segfault in lldbRecorder.py
        #self.assertEqual(0, proc.returncode)
        self.assertEqual("", err)
        self.assertEqual('[\n  {\n    "name": "sort(int*, int)", \n    "calls": [\n      {\n        "name": "quicksort(int*, int, int)"\n      }\n    ]\n  }\n]\n', out)

if __name__ == "__main__":
    unittest.main()
