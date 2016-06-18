import os
import shutil
import subprocess
import tempfile
import unittest

class TestIntegration(unittest.TestCase):

    def testBrokenQuicksortExample(self):
        try:
            # Use a temporary scratch directory.
            tempOutputDir = tempfile.mkdtemp()

            executable = "examples/brokenQuicksort/out/brokenQuicksort"
            goodInput = "1 6 3 9 0"
            goodCctFile = os.path.join(tempOutputDir, "good.json")
            badInput = "1 6 5 9 0"
            badCctFile = os.path.join(tempOutputDir, "bad.json")

            # Record good and bad runs.
            lldbSteps = [
                "command script import recordCommand.py",
                "breakpoint set --name sort",
                "run " + goodInput,
                "record --output=" + goodCctFile,
                "continue",
                "run " + badInput,
                "record --output=" + badCctFile,
                "c",
                "q"
            ]
            command = "lldb " + executable + " " + (' '.join("-o \"" + step + "\"" for step in lldbSteps))
            proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            self.assertEqual("", err)

            # Compare the two runs.
            command = "./compare.py " + goodCctFile + " " + badCctFile
            proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            self.assertEqual("", err)
            self.assertEqual(badCctFile + " diverged from " + goodCctFile + " in 1 places:"
                "\n  swap(int*, int, int) which was called by quicksort(int*, int, int)\n", out)
        finally:
            shutil.rmtree(tempOutputDir)

if __name__ == "__main__":
    unittest.main()
