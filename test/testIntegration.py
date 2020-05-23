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

            executable = "test/data/out/brokenQuicksort"
            goodInput = "1 6 3 9 0"
            goodRecording = os.path.join(tempOutputDir, "good.txt")
            badInput = "1 6 5 9 0"
            badRecording = os.path.join(tempOutputDir, "bad.txt")

            # Record good run.
            environment = os.environ.copy()
            environment["RECORD_CCT"] = goodRecording
            proc = subprocess.Popen(executable + " " + goodInput, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=environment)
            out, err = proc.communicate()
            if not os.path.isfile(goodRecording):
                raise AssertionError("Recording was not saved to \"" + goodRecording + "\"" + (": " + err if err else ""))

            # Record bad run.
            environment = os.environ.copy()
            environment["RECORD_CCT"] = badRecording
            proc = subprocess.Popen(executable + " " + badInput, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=environment)
            out, err = proc.communicate()
            if not os.path.isfile(badRecording):
                raise AssertionError("Recording was not saved to \"" + badRecording + "\"" + (": " + err if err else ""))

            # Compare the two runs.
            command = "./compare.py " + goodRecording + " " + badRecording
            proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            self.assertEqual("", err)
            self.assertEqual(badRecording + " diverged from " + goodRecording + " in 1 places:"
                "\n  _Z4swapPiii which was called by _Z9quicksortPiii\n", out)
        finally:
            shutil.rmtree(tempOutputDir)

if __name__ == "__main__":
    unittest.main()
