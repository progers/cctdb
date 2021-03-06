from cct import CCT, Function
import os
import shutil
import subprocess
import tempfile
import unittest

class TestRecord(unittest.TestCase):

    def _record(self, executable, argsList = None):
        try:
            # Use a temporary scratch directory.
            tempOutputDir = tempfile.mkdtemp()
            outputFile = os.path.join(tempOutputDir, "cct.txt")

            command = [ executable ]
            if argsList:
                command.extend(argsList)
            environment = os.environ.copy()
            environment["RECORD_CCT"] = outputFile
            proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=environment)
            out, err = proc.communicate()

            # Ensure the recording was written.
            if not os.path.isfile(outputFile):
                raise AssertionError("Recording not saved to \"" + outputFile + "\"" + (": " + err if err else ""))

            with open (outputFile, 'r') as inFile:
                record = inFile.read()
            return record
        finally:
            shutil.rmtree(tempOutputDir)

    def _stripThreadIds(self, records):
        strippedRecords = []
        for record in iter(records.splitlines()):
            if record.startswith("tid"):
                firstSpace = record.find(' ')
                if firstSpace != -1:
                    record = record[firstSpace+1:]
            strippedRecords.append(record)
        return '\n'.join(strippedRecords)

    def testBasicRecordingAtMain(self):
        record = self._record("test/data/out/quicksort", ["1"])
        record = self._stripThreadIds(record)
        self.assertEquals(record, "entering main\nentering _Z4sortPii\nentering _Z9quicksortPiii\nexiting _Z9quicksortPiii\nexiting _Z4sortPii\nexiting main")

    @unittest.skipUnless(os.uname()[0] == "Darwin", "requires Darwin")
    def testRecordWithDynamicLibrary(self):
        record = self._record("test/data/out/dynamicLoaderDarwin")
        self.assertEquals(CCT.fromRecord(record).asJson(), '[{"name": "main", "calls": [{"name": "create", "calls": [{"name": "_ZN18DynamicClassDarwinC1Ev", "calls": [{"name": "_ZN18DynamicClassDarwinC2Ev"}]}]}, {"name": "_ZN18DynamicClassDarwin13dynamicCallABEv", "calls": [{"name": "_ZN18DynamicClassDarwin5callAEv"}, {"name": "_ZN18DynamicClassDarwin5callBEv"}]}, {"name": "destroy", "calls": [{"name": "_ZN18DynamicClassDarwinD0Ev", "calls": [{"name": "_ZN18DynamicClassDarwinD1Ev", "calls": [{"name": "_ZN18DynamicClassDarwinD2Ev"}]}]}]}, {"name": "_Z11notDynamicCv"}]}]')

    def testRecordingWithThreads(self):
        record = self._record("test/data/out/fibonacciThread", ["2"])
        # computeFibonacciUsingJustOneThread should have been called 3 times.
        self.assertEquals(record.count("entering _Z34computeFibonacciUsingJustOneThreadmm"), 3)
        self.assertEquals(record.count("exiting _Z34computeFibonacciUsingJustOneThreadmm"), 3)

    def testSingleInstructionInline(self):
        record = self._record("test/data/out/singleInstructionInline")
        self.assertEquals(CCT.fromRecord(record).asJson(), '[{"name": "main", "calls": [{"name": "_Z1Av", "calls": [{"name": "_Z7inlineBv", "calls": [{"name": "_Z1Cv", "calls": [{"name": "_Z1Dv"}]}]}]}]}]')

if __name__ == "__main__":
    unittest.main()
