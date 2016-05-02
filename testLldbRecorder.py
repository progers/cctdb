#!/usr/bin/env python

from lldbRecorder import lldbRecorder
import platform
import subprocess
import unittest
import warnings

class TestLldbRecorder(unittest.TestCase):

    def testBrokenExecutable(self):
        with self.assertRaises(Exception) as cm:
            lldbRecorder("does/not/exist")
        self.assertEqual(cm.exception.message, "Could not create target 'does/not/exist'")

    def testGetModuleNames(self):
        moduleNames = lldbRecorder("testData/quicksort").getModuleNames()
        self.assertIn("dyld", moduleNames)
        self.assertIn("libc++abi.dylib", moduleNames)
        quicksortModuleFound = False
        for moduleName in moduleNames:
            if "quicksort" in moduleName:
                quicksortModuleFound = True
                break
        self.assertTrue(quicksortModuleFound)

    def testGetAllFunctions(self):
        functionNames = lldbRecorder("testData/quicksort").getAllFunctionNames()
        self.assertIn("main", functionNames)
        self.assertIn("swap(int*, int, int)", functionNames)
        self.assertIn("quicksort(int*, int, int)", functionNames)
        self.assertIn("fgets", functionNames)
        self.assertIn("printf", functionNames)

    def testGetFunctionNamesWithModuleName(self):
        recorder = lldbRecorder("testData/quicksort")
        quicksortModuleName = recorder.getModuleNames()[0]
        self.assertIn("quicksort", quicksortModuleName)
        functionNames = recorder.getFunctionNamesWithModuleName(quicksortModuleName)
        self.assertIn("main", functionNames)
        self.assertIn("swap(int*, int, int)", functionNames)
        self.assertIn("quicksort(int*, int, int)", functionNames)

    def testRecordMissingModule(self):
        with self.assertRaises(Exception) as cm:
            recorder = lldbRecorder("testData/quicksort")
            cct = recorder.launchProcessThenRecord(["1"], "ModuleThatDoesNotExist")
        self.assertIn("Unable to find specified module in target.", cm.exception.message)

    def testRecordMissingFunction(self):
        recorder = lldbRecorder("testData/fibonacci")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacci", moduleName)

        with self.assertRaises(Exception) as cm:
            cct = recorder.launchProcessThenRecord(["3"], moduleName, "functionDoesNotExist")
        self.assertIn("Function 'functionDoesNotExist' was not found.", cm.exception.message)

    def testBasicRecordingAtMain(self):
        recorder = lldbRecorder("testData/quicksort")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("quicksort", moduleName)

        cct = recorder.launchProcessThenRecord(["1"], moduleName)
        self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)"}]}]}]')

    def testBasicRecordingAtSubroutine(self):
        moduleName = lldbRecorder("testData/quicksort").getModuleNames()[0]
        self.assertIn("quicksort", moduleName)

        sortCct = lldbRecorder("testData/quicksort").launchProcessThenRecord(["1", "3", "2"], moduleName, "sort(int*, int)")
        self.assertEquals(sortCct.asJson(), '[{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)", "calls": [{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "quicksort(int*, int, int)"}, {"name": "quicksort(int*, int, int)"}]}]}]')

        partitionCct = lldbRecorder("testData/quicksort").launchProcessThenRecord(["1", "3", "2"], moduleName, "partition(int*, int, int)")
        self.assertEquals(partitionCct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')

        swapCct = lldbRecorder("testData/quicksort").launchProcessThenRecord(["1", "3", "2"], moduleName, "swap(int*, int, int)")
        self.assertEquals(swapCct.asJson(), '[{"name": "swap(int*, int, int)"}]')

    def testMultipleCallsToTargetFunction(self):
        recorder = lldbRecorder("testData/quicksort")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("quicksort", moduleName)

        cct = recorder.launchProcessThenRecord(["3", "1", "2", "3", "2"], moduleName, "partition(int*, int, int)")
        self.assertEquals(cct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)"}]')

    def testRecordProcess(self):
        executable = "testData/fibonacci"
        recorder = lldbRecorder(executable)
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacci", moduleName)

        proc = subprocess.Popen(executable + " 3", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        cct = recorder.attachToProcessThenRecord(proc.pid, moduleName, "computeFibonacci(unsigned long)")
        self.assertEquals(cct.asJson(), '[{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}]')
        self.assertIn("Fibonacci number 3 is 2", proc.stdout.read())

    def testRecordingWithThreads(self):
        executable = "testData/fibonacciThread"
        moduleName = lldbRecorder(executable).getModuleNames()[0]
        self.assertIn("fibonacciThread", moduleName)

        cct = lldbRecorder(executable).launchProcessThenRecord(["3"], moduleName, "computeFibonacci(unsigned long)")
        self.assertEquals(3, len(cct.calls))
        # Each call to computeFibonacci should have the same subtree.
        firstCall = cct.calls[0]
        self.assertEquals(firstCall.asJson(), '{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}')
        self.assertEquals(firstCall.asJson(), cct.calls[1].asJson())
        self.assertEquals(firstCall.asJson(), cct.calls[2].asJson())

        # Recording the subtrees starting at fib(unsigned long) should work as well.
        cct = lldbRecorder(executable).launchProcessThenRecord(["3"], moduleName, "fib(unsigned long)")
        self.assertEquals(3, len(cct.calls))
        firstCall = cct.calls[0]
        self.assertEquals(firstCall.asJson(), '{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}')
        self.assertEquals(firstCall.asJson(), cct.calls[1].asJson())
        self.assertEquals(firstCall.asJson(), cct.calls[2].asJson())

    # Not supported! See comment in lldbRecorder.py::_recordSubtreeCallsFromThread.
    # This test checks for assertions and that that recording works as if new threads never existed.
    def testRecordingIntoNewThreads(self):
        recorder = lldbRecorder("testData/fibonacciThread")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacciThread", moduleName)

        cct = recorder.launchProcessThenRecord(["3"], moduleName, "main")
        self.assertEquals(cct.asJson(), '[{"name": "main"}]')

    def testComplexInlinedTree(self):
        recorder = lldbRecorder("testData/complexInlinedTree")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("complexInlinedTree", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "A(int&)")
        self.assertEquals(len(cct.calls), 2)

        # Branch 0
        self.assertEquals(cct.calls[0].asJson(), '{"name": "A(int&)", "calls": [{"name": "C(int&)", "calls": [{"name": "A(int&)", "calls": [{"name": "A(int&)"}]}]}]}')
        # Branch 1
        self.assertEquals(cct.calls[1].asJson(), '{"name": "A(int&)"}')

    def testComplexInlinedTreeWithDeepBreakpoint(self):
        recorder = lldbRecorder("testData/complexInlinedTree")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("complexInlinedTree", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "C(int&)")
        self.assertEquals(len(cct.calls), 1)
        self.assertEquals(cct.calls[0].asJson(), '{"name": "C(int&)", "calls": [{"name": "A(int&)", "calls": [{"name": "A(int&)"}]}]}')

    def testComplexInlinedCases(self):
        recorder = lldbRecorder("testData/complexInlinedCases")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("complexInlinedCases", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "A(int&)")
        self.assertEquals(len(cct.calls), 3)

        # Branch 0
        self.assertEquals(cct.calls[0].asJson(), '{"name": "A(int&)", "calls": [{"name": "C(int&)"}]}')
        # Branch 1
        self.assertEquals(cct.calls[1].asJson(), '{"name": "A(int&)"}')
        # Branch 2
        #  empty
        # Branch 3
        self.assertEquals(cct.calls[2].asJson(), '{"name": "A(int&)"}')

    def testSingleInstructionInline(self):
        recorder = lldbRecorder("testData/singleInstructionInline")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("singleInstructionInline", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "A()")
        self.assertEquals(cct.asJson(), '[{"name": "A()", "calls": [{"name": "C()", "calls": [{"name": "D()"}]}]}]')

if __name__ == "__main__":
    if platform.system() != "Darwin":
        warnings.warn("Platform '" + str(platform.system()) + "' may not support the full lldb API")
    unittest.main()
