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

    def testMultipleCallsToTargetFunction(self):
        recorder = lldbRecorder("examples/brokenQuicksort/brokenQuicksort")
        brokenQuicksortModuleName = recorder.getModuleNames()[0]
        self.assertIn("brokenQuicksort", brokenQuicksortModuleName)

        cct = recorder.launchProcessThenRecord(["3", "1", "2", "3", "2"], brokenQuicksortModuleName, "partition(int*, int, int)")
        self.assertEquals(cct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)"}]')

    def testRecordProcess(self):
        executable = "testData/fibonacci"
        recorder = lldbRecorder(executable)
        fibonacciModuleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacci", fibonacciModuleName)

        proc = subprocess.Popen(executable + " 3", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        cct = recorder.attachToProcessThenRecord(proc.pid, fibonacciModuleName, "computeFibonacci(unsigned long)")
        self.assertEquals(cct.asJson(), '[{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}]')
        self.assertIn("Fibonacci number 3 is 2", proc.stdout.read())

    def testRecordingWithThreads(self):
        executable = "testData/fibonacciThread"
        fibonacciModuleName = lldbRecorder(executable).getModuleNames()[0]
        self.assertIn("fibonacciThread", fibonacciModuleName)

        cct = lldbRecorder(executable).launchProcessThenRecord(["3"], fibonacciModuleName, "computeFibonacci(unsigned long)")
        self.assertEquals(3, len(cct.calls))
        # Each call to computeFibonacci should have the same subtree.
        firstCall = cct.calls[0]
        self.assertEquals(firstCall.asJson(), '{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}')
        self.assertEquals(firstCall.asJson(), cct.calls[1].asJson())
        self.assertEquals(firstCall.asJson(), cct.calls[2].asJson())

        # Recording the subtrees starting at fib(unsigned long) should work as well.
        cct = lldbRecorder(executable).launchProcessThenRecord(["3"], fibonacciModuleName, "fib(unsigned long)")
        self.assertEquals(3, len(cct.calls))
        firstCall = cct.calls[0]
        self.assertEquals(firstCall.asJson(), '{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}')
        self.assertEquals(firstCall.asJson(), cct.calls[1].asJson())
        self.assertEquals(firstCall.asJson(), cct.calls[2].asJson())

    # Not supported! See comment in lldbHelper.py::_recordSubtreeCallsFromThread.
    # This test checks for assertions and that that recording works as if new threads never existed.
    def testRecordingIntoNewThreads(self):
        recorder = lldbRecorder("testData/fibonacciThread")
        fibonacciThreadModuleName = recorder.getModuleNames()[0];
        self.assertIn("fibonacciThread", fibonacciThreadModuleName)

        cct = recorder.launchProcessThenRecord(["3"], fibonacciThreadModuleName, "main")
        self.assertEquals(cct.asJson(), '[{"name": "main"}]')

if __name__ == "__main__":
    if platform.system() != "Darwin":
        warnings.warn("Platform '" + str(platform.system()) + "' may not support the full lldb API")
    unittest.main()
