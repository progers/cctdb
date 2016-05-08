#!/usr/bin/env python

from lldbRecorder import lldbRecorder
import gc
import os
import platform
import subprocess
import unittest
import warnings

class TestLldbRecorder(unittest.TestCase):

    # The LLDB python interface will segfault on teardown if the teardown process is not controlled.
    # ("Python quit unexpectedly while using the _lldb.so plugin.", EXC_BAD_ACCESS (SIGSEGV))
    # See: https://llvm.org/bugs/show_bug.cgi?id=27639
    #
    # To workaround this, we keep track of all recorders and only free them once at the end of all
    # test runs. All tests must use createTestRecorder instead of using the lldbRecorder ctor.
    @classmethod
    def createTestRecorder(self, executable):
        recorder = lldbRecorder(executable)
        self._recorders.append(recorder)
        return recorder

    # (See comment above createTestRecorder for why this is needed.)
    @classmethod
    def setUpClass(self):
        self._recorders = []

    # (See comment above createTestRecorder for why this is needed.)
    # This teardown approach is based on lldb's python api test suite in TestBase.tearDown from
    # .../packages/Python/lldbsuite/test/lldbtest.py
    @classmethod
    def tearDownClass(self):
        # Ensure all the references to SB objects have gone away so that we can be sure that all
        # test-specific resources have been freed before we attempt to delete the targets.
        gc.collect()

        # Delete the target(s) from the debugger as a general cleanup step. This includes
        # terminating the process for each target.
        for recorder in self._recorders:
            target = recorder._target
            if target:
                process = target.GetProcess()
                if process:
                    process.Kill()
        del self._recorders

    def testBrokenExecutable(self):
        with self.assertRaises(Exception) as cm:
            self.createTestRecorder("does/not/exist")
        self.assertEqual(cm.exception.message, "Could not create target 'does/not/exist'")

    def testGetModuleNames(self):
        moduleNames = self.createTestRecorder("testData/quicksort").getModuleNames()
        self.assertIn("/usr/lib/dyld", moduleNames)
        quicksortModuleFound = False
        for moduleName in moduleNames:
            if "quicksort" in moduleName:
                quicksortModuleFound = True
                break
        self.assertTrue(quicksortModuleFound)

    def testGetAllFunctions(self):
        functionNames = self.createTestRecorder("testData/quicksort").getAllFunctionNames()
        self.assertIn("main", functionNames)
        self.assertIn("swap(int*, int, int)", functionNames)
        self.assertIn("quicksort(int*, int, int)", functionNames)
        self.assertIn("fgets", functionNames)
        self.assertIn("printf", functionNames)

    def testGetAllFunctionNamesInLoadedLibrary(self):
        recorder = self.createTestRecorder("testData/dynamicLoaderDarwin")
        functionNamesBeforeLoading = recorder.getAllFunctionNames()
        self.assertIn("notDynamicC()", functionNamesBeforeLoading)
        self.assertNotIn("dynamicCallAB()", functionNamesBeforeLoading)

    def testGetFunctionNamesWithModuleName(self):
        recorder = self.createTestRecorder("testData/quicksort")
        quicksortModuleName = recorder.getModuleNames()[0]
        self.assertIn("quicksort", quicksortModuleName)
        functionNames = recorder.getFunctionNamesWithModuleName(quicksortModuleName)
        self.assertIn("main", functionNames)
        self.assertIn("swap(int*, int, int)", functionNames)
        self.assertIn("quicksort(int*, int, int)", functionNames)

    def testRecordMissingModule(self):
        with self.assertRaises(Exception) as cm:
            self.createTestRecorder("testData/quicksort").launchProcessThenRecord(["1"], "ModuleThatDoesNotExist")
        self.assertIn("Unable to find specified module in target.", cm.exception.message)

    def testRecordMissingModuleInLoadedLibrary(self):
        executable = "testData/dynamicLoaderDarwin"
        proc = subprocess.Popen(executable, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        with self.assertRaises(Exception) as cm:
            self.createTestRecorder(executable).attachToProcessThenRecord(proc.pid, "dynamicModuleDoesNotExist", "DynamicClassDarwin::dynamicCallAB()")
        self.assertEquals("Unable to find specified module in target.", cm.exception.message)

    def testRecordMissingFunction(self):
        recorder = self.createTestRecorder("testData/fibonacci")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacci", moduleName)

        with self.assertRaises(Exception) as cm:
            recorder.launchProcessThenRecord(["3"], moduleName, "functionDoesNotExist")
        self.assertIn("Could not break on function. Check the specified function name.", cm.exception.message)

    def testRecordMissingFunctionInLoadedLibrary(self):
        executable = "testData/dynamicLoaderDarwin"
        recorder = self.createTestRecorder(executable)
        moduleName = recorder.getModuleNames()[0]
        functionNotInModule = "DynamicClassDarwin::dynamicCallAB()"
        proc = subprocess.Popen(executable, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        with self.assertRaises(Exception) as cm:
            recorder.attachToProcessThenRecord(proc.pid, moduleName, functionNotInModule)
        self.assertEquals("Could not break on function. Check the specified function name.", cm.exception.message)

    def testBasicRecordingAtMain(self):
        recorder = self.createTestRecorder("testData/quicksort")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("quicksort", moduleName)

        cct = recorder.launchProcessThenRecord(["1"], moduleName)
        self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)"}]}]}]')

    def testBasicRecordingAtSubroutine(self):
        moduleName = self.createTestRecorder("testData/quicksort").getModuleNames()[0]
        self.assertIn("quicksort", moduleName)

        sortCct = self.createTestRecorder("testData/quicksort").launchProcessThenRecord(["1", "3", "2"], moduleName, "sort(int*, int)")
        self.assertEquals(sortCct.asJson(), '[{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)", "calls": [{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "quicksort(int*, int, int)"}, {"name": "quicksort(int*, int, int)"}]}]}]')

        partitionCct = self.createTestRecorder("testData/quicksort").launchProcessThenRecord(["1", "3", "2"], moduleName, "partition(int*, int, int)")
        self.assertEquals(partitionCct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')

        swapCct = self.createTestRecorder("testData/quicksort").launchProcessThenRecord(["1", "3", "2"], moduleName, "swap(int*, int, int)")
        self.assertEquals(swapCct.asJson(), '[{"name": "swap(int*, int, int)"}]')

    def testMultipleCallsToTargetFunction(self):
        recorder = self.createTestRecorder("testData/quicksort")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("quicksort", moduleName)

        cct = recorder.launchProcessThenRecord(["3", "1", "2", "3", "2"], moduleName, "partition(int*, int, int)")
        self.assertEquals(cct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)"}]')

    def testRecordProcess(self):
        executable = "testData/fibonacci"
        recorder = self.createTestRecorder(executable)
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacci", moduleName)

        proc = subprocess.Popen(executable + " 3", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        cct = recorder.attachToProcessThenRecord(proc.pid, moduleName, "computeFibonacci(unsigned long)")
        self.assertEquals(cct.asJson(), '[{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}]')
        self.assertIn("Fibonacci number 3 is 2", proc.stdout.read())

    def testRecordLoadedLibrary(self):
        executable = "testData/dynamicLoaderDarwin"
        dynamicModuleName = os.getcwd() + "/testData/dynamicClassDarwin.so"
        recorder = self.createTestRecorder(executable)

        moduleNamesBeforeLoading = recorder.getModuleNames()
        self.assertIn("dynamicLoaderDarwin", moduleNamesBeforeLoading[0])
        self.assertNotIn(dynamicModuleName, moduleNamesBeforeLoading)

        proc = subprocess.Popen(executable, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        cct = recorder.attachToProcessThenRecord(proc.pid, dynamicModuleName, "DynamicClassDarwin::dynamicCallAB()")
        self.assertEquals(cct.asJson(), '[{"name": "DynamicClassDarwin::dynamicCallAB()", "calls": [{"name": "DynamicClassDarwin::callA()"}, {"name": "DynamicClassDarwin::callB()"}]}]')

    def testRecordStaysInSpecifiedLibrary(self):
        executable = "testData/dynamicLoaderDarwin"
        recorder = self.createTestRecorder(executable)
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("dynamicLoaderDarwin", moduleName)

        cct = self.createTestRecorder(executable).launchProcessThenRecord([], moduleName, "main")
        # Ensure no DynamicClassDarwin calls are in the tree.
        self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "notDynamicC()"}]}]')

    @unittest.skip("FIXME(phil): support thread stepping in with new event-based recording.")
    def testRecordingWithThreads(self):
        executable = "testData/fibonacciThread"
        moduleName = self.createTestRecorder(executable).getModuleNames()[0]
        self.assertIn("fibonacciThread", moduleName)

        cct = self.createTestRecorder(executable).launchProcessThenRecord(["3"], moduleName, "computeFibonacci(unsigned long)")
        self.assertEquals(3, len(cct.calls))
        # Each call to computeFibonacci should have the same subtree.
        firstCall = cct.calls[0]
        self.assertEquals(firstCall.asJson(), '{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}')
        self.assertEquals(firstCall.asJson(), cct.calls[1].asJson())
        self.assertEquals(firstCall.asJson(), cct.calls[2].asJson())

        # Recording the subtrees starting at fib(unsigned long) should work as well.
        cct = self.createTestRecorder(executable).launchProcessThenRecord(["3"], moduleName, "fib(unsigned long)")
        self.assertEquals(3, len(cct.calls))
        firstCall = cct.calls[0]
        self.assertEquals(firstCall.asJson(), '{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}')
        self.assertEquals(firstCall.asJson(), cct.calls[1].asJson())
        self.assertEquals(firstCall.asJson(), cct.calls[2].asJson())

    # Not supported! See comment in lldbRecorder.py::_recordSubtreeCallsFromThread.
    # This test checks for assertions and that that recording works as if new threads never existed.
    def testRecordingIntoNewThreads(self):
        recorder = self.createTestRecorder("testData/fibonacciThread")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("fibonacciThread", moduleName)

        cct = recorder.launchProcessThenRecord(["3"], moduleName, "main")
        self.assertEquals(cct.asJson(), '[{"name": "main"}]')

    def testComplexInlinedTree(self):
        recorder = self.createTestRecorder("testData/complexInlinedTree")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("complexInlinedTree", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "A(int&)")
        self.assertEquals(len(cct.calls), 2)

        # Branch 0
        self.assertEquals(cct.calls[0].asJson(), '{"name": "A(int&)", "calls": [{"name": "C(int&)", "calls": [{"name": "A(int&)", "calls": [{"name": "A(int&)"}]}]}]}')
        # Branch 1
        self.assertEquals(cct.calls[1].asJson(), '{"name": "A(int&)"}')

    def testComplexInlinedTreeWithDeepBreakpoint(self):
        recorder = self.createTestRecorder("testData/complexInlinedTree")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("complexInlinedTree", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "C(int&)")
        self.assertEquals(len(cct.calls), 1)
        self.assertEquals(cct.calls[0].asJson(), '{"name": "C(int&)", "calls": [{"name": "A(int&)", "calls": [{"name": "A(int&)"}]}]}')

    def testComplexInlinedCases(self):
        recorder = self.createTestRecorder("testData/complexInlinedCases")
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
        recorder = self.createTestRecorder("testData/singleInstructionInline")
        moduleName = recorder.getModuleNames()[0]
        self.assertIn("singleInstructionInline", moduleName)

        cct = recorder.launchProcessThenRecord([], moduleName, "A()")
        self.assertEquals(cct.asJson(), '[{"name": "A()", "calls": [{"name": "C()", "calls": [{"name": "D()"}]}]}]')

if __name__ == "__main__":
    if platform.system() != "Darwin":
        warnings.warn("Platform '" + str(platform.system()) + "' may not support the full lldb API")
    unittest.main()
