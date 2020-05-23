import os
import shutil
import subprocess
import tempfile
import unittest

class TestIntegration(unittest.TestCase):

    def testBrokenQuicksortExample(self):
        outputFile = "record.txt"
        goodOutputFile = "good_record.txt"
        badOutputFile = "bad_record.txt"
        # Don't step on an existing file.
        if os.path.isfile(outputFile):
            raise AssertionError("Recording already exists: " + outputFile)
        if os.path.isfile(goodOutputFile):
            raise AssertionError("Recording already exists: " + goodOutputFile)
        if os.path.isfile(badOutputFile):
            raise AssertionError("Recording already exists: " + badOutputFile)

        try:
            executable = "test/data/out/brokenQuicksort"
            goodInput = "1 6 3 9 0"
            badInput = "1 6 5 9 0"

            # Record good run.
            proc = subprocess.Popen(executable + " " + goodInput, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            self.assertEqual("", err)
            shutil.copyfile(outputFile, goodOutputFile)

            # Record bad run.
            proc = subprocess.Popen(executable + " " + badInput, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            self.assertEqual("", err)
            shutil.copyfile(outputFile, badOutputFile)

            # Compare the two runs.
            command = "./compare.py " + goodOutputFile + " " + badOutputFile
            proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            self.assertEqual("", err)
            self.assertEqual(badOutputFile + " diverged from " + goodOutputFile + " in 1 places:"
                "\n  _Z4swapPiii which was called by _Z9quicksortPiii\n", out)
        finally:
            os.remove(outputFile)
            os.remove(goodOutputFile)
            os.remove(badOutputFile)

if __name__ == "__main__":
    unittest.main()
