#!/usr/bin/env python

from lldbRecorder import lldbRecorder
import platform
import subprocess
import unittest
import warnings

class TestLldbRecorder(unittest.TestCase):

    def testBrokenExecutable(self):
        with self.assertRaises(Exception) as cm:
            lldbRecorder("does/not/exist").launchProcess()
        self.assertEqual(cm.exception.message, "Could not create target 'does/not/exist'")

    def testGetModuleNames(self):
        moduleNames = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").getModuleNames()
        self.assertIn("dyld", moduleNames)
        self.assertIn("libc++abi.dylib", moduleNames)
        brokenQuicksortModuleFound = False
        for moduleName in moduleNames:
            if "brokenQuicksort" in moduleName:
                brokenQuicksortModuleFound = True
                break
        self.assertTrue(brokenQuicksortModuleFound)

    def testGetAllFunctions(self):
        functionNames = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").getAllFunctionNames()
        self.assertIn("main", functionNames)
        self.assertIn("swap(int*, int, int)", functionNames)
        self.assertIn("quicksort(int*, int, int)", functionNames)
        self.assertIn("fgets", functionNames)
        self.assertIn("printf", functionNames)

    def testGetFunctionNamesWithModuleName(self):
        recorder = lldbRecorder("examples/brokenQuicksort/brokenQuicksort")
        brokenQuicksortModuleName = recorder.getModuleNames()[0]
        self.assertIn("brokenQuicksort", brokenQuicksortModuleName)
        functionNames = recorder.getFunctionNamesWithModuleName(brokenQuicksortModuleName)
        self.assertIn("main", functionNames)
        self.assertIn("swap(int*, int, int)", functionNames)
        self.assertIn("quicksort(int*, int, int)", functionNames)

    def testRecordMissingModule(self):
        with self.assertRaises(Exception) as cm:
            recorder = lldbRecorder("examples/brokenQuicksort/brokenQuicksort")
            cct = recorder.launchProcessThenRecord(["1"], "ModuleThatDoesNotExist")
        self.assertIn("Unable to find specified module in target.", cm.exception.message)

    def testRecordMissingFunction(self):
        recorder = lldbRecorder("testData/fibonacci")
        fibonacciModuleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacci", fibonacciModuleName)

        with self.assertRaises(Exception) as cm:
            cct = recorder.launchProcessThenRecord(["3"], fibonacciModuleName, "functionDoesNotExist")
        self.assertIn("Function 'functionDoesNotExist' was not found.", cm.exception.message)

    def testBasicRecordingAtMain(self):
        recorder = lldbRecorder("examples/brokenQuicksort/brokenQuicksort")
        brokenQuicksortModuleName = recorder.getModuleNames()[0]
        self.assertIn("brokenQuicksort", brokenQuicksortModuleName)

        cct = recorder.launchProcessThenRecord(["1"], brokenQuicksortModuleName)
        self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)"}]}]}]')

    def testBasicRecordingAtSubroutine(self):
        brokenQuicksortModuleName = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").getModuleNames()[0]
        self.assertIn("brokenQuicksort", brokenQuicksortModuleName)

        sortCct = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").launchProcessThenRecord(["1", "3", "2"], brokenQuicksortModuleName, "sort(int*, int)")
        self.assertEquals(sortCct.asJson(), '[{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)", "calls": [{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "quicksort(int*, int, int)"}, {"name": "quicksort(int*, int, int)"}]}]}]')

        partitionCct = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").launchProcessThenRecord(["1", "3", "2"], brokenQuicksortModuleName, "partition(int*, int, int)")
        self.assertEquals(partitionCct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')

        swapCct = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").launchProcessThenRecord(["1", "3", "2"], brokenQuicksortModuleName, "swap(int*, int, int)")
        self.assertEquals(swapCct.asJson(), '[{"name": "swap(int*, int, int)"}]')

if __name__ == "__main__":
    if platform.system() != "Darwin":
        warnings.warn("Platform '" + str(platform.system()) + "' may not support the full lldb API")
    unittest.main()
