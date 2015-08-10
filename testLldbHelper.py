#!/usr/bin/env python

import lldbHelper
import platform
import subprocess
import unittest
import warnings

class TestLldbHelper(unittest.TestCase):

    def testBrokenExecutable(self):
        with self.assertRaises(Exception) as cm:
            lldbHelper.listModules("does/not/exist")
        self.assertEqual(cm.exception.message, "Error creating target 'does/not/exist'")

    def testBadModule(self):
        if platform.system() == "Darwin":
            executable = "examples/brokenQuicksort/brokenQuicksort"
            modules = lldbHelper.listModules(executable)
            with self.assertRaises(Exception) as cm:
                cct = lldbHelper.recordCommand(executable, ["1"], "ModuleThatDoesNotExist", "main")
            self.assertIn("Unable to find specified module in target.", cm.exception.message)
        else:
            warnings.warn("Platform not supported for this test")

    def testListModules(self):
        if platform.system() == "Darwin":
            modules = lldbHelper.listModules("examples/brokenQuicksort/brokenQuicksort")
            self.assertIn("/usr/lib/dyld", modules)
            self.assertIn("/usr/lib/libc++abi.dylib", modules)
            brokenQuicksortModuleFound = False
            for module in modules:
                if "examples/brokenQuicksort/brokenQuicksort" in module:
                    brokenQuicksortModuleFound = True
                    break
            self.assertTrue(brokenQuicksortModuleFound)
        else:
            warnings.warn("Platform not supported for this test")

    def testListFunctionsWithModule(self):
        if platform.system() == "Darwin":
            modules = lldbHelper.listModules("examples/brokenQuicksort/brokenQuicksort")
            brokenQuicksortModule = modules[0];
            self.assertIn("brokenQuicksort", brokenQuicksortModule)
            functions = lldbHelper.listFunctions("examples/brokenQuicksort/brokenQuicksort", brokenQuicksortModule)
            self.assertIn("main", functions);
            self.assertIn("swap(int*, int, int)", functions)
            self.assertIn("quicksort(int*, int, int)", functions);
        else:
            warnings.warn("Platform not supported for this test")

    def testListAllFunctions(self):
        if platform.system() == "Darwin":
            functions = lldbHelper.listFunctions("examples/brokenQuicksort/brokenQuicksort")
            self.assertIn("main", functions);
            self.assertIn("swap(int*, int, int)", functions)
            self.assertIn("quicksort(int*, int, int)", functions);
            self.assertIn("fgets", functions);
            self.assertIn("printf", functions);
        else:
            warnings.warn("Platform not supported for this test")

    def testBadFunction(self):
        if platform.system() == "Darwin":
            executable = "testData/fibonacci"
            modules = lldbHelper.listModules(executable)
            fibonacciModule = modules[0];
            self.assertIn("fibonacci", fibonacciModule)

            with self.assertRaises(Exception) as cm:
                cct = lldbHelper.recordCommand(executable, ["3"], fibonacciModule, "functionDoesNotExist")
            self.assertIn("Function 'functionDoesNotExist' was not found.", cm.exception.message)
        else:
            warnings.warn("Platform not supported for this test")

    def testBasicRecordingAtMain(self):
        if platform.system() == "Darwin":
            executable = "examples/brokenQuicksort/brokenQuicksort"
            modules = lldbHelper.listModules(executable)
            brokenQuicksortModule = modules[0];
            self.assertIn("brokenQuicksort", brokenQuicksortModule)

            cct = lldbHelper.recordCommand(executable, ["1"], brokenQuicksortModule, "main")
            self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)"}]}]}]')
        else:
            warnings.warn("Platform not supported for this test")

    def testBasicRecordingAtSubroutine(self):
        if platform.system() == "Darwin":
            executable = "examples/brokenQuicksort/brokenQuicksort"
            modules = lldbHelper.listModules(executable)
            brokenQuicksortModule = modules[0];
            self.assertIn("brokenQuicksort", brokenQuicksortModule)

            sortCct = lldbHelper.recordCommand(executable, ["1", "3", "2"], brokenQuicksortModule, "sort(int*, int)")
            self.assertEquals(sortCct.asJson(), '[{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)", "calls": [{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "quicksort(int*, int, int)"}, {"name": "quicksort(int*, int, int)"}]}]}]')

            partitionCct = lldbHelper.recordCommand(executable, ["1", "3", "2"], brokenQuicksortModule, "partition(int*, int, int)")
            self.assertEquals(partitionCct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')

            swapCct = lldbHelper.recordCommand(executable, ["1", "3", "2"], brokenQuicksortModule, "swap(int*, int, int)")
            self.assertEquals(swapCct.asJson(), '[{"name": "swap(int*, int, int)"}]')
        else:
            warnings.warn("Platform not supported for this test")

    def testMultipleCallsToTargetFunction(self):
        if platform.system() == "Darwin":
            executable = "examples/brokenQuicksort/brokenQuicksort"
            modules = lldbHelper.listModules(executable)
            brokenQuicksortModule = modules[0];
            self.assertIn("brokenQuicksort", brokenQuicksortModule)

            cct = lldbHelper.recordCommand(executable, ["3", "1", "2", "3", "2"], brokenQuicksortModule, "partition(int*, int, int)")
            self.assertEquals(cct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "partition(int*, int, int)"}]')
        else:
            warnings.warn("Platform not supported for this test")

    def testRecordProcess(self):
        if platform.system() == "Darwin":
            executable = "testData/fibonacci"
            modules = lldbHelper.listModules(executable)
            fibonacciModule = modules[0];
            self.assertIn("fibonacci", fibonacciModule)

            proc = subprocess.Popen(executable + " 3", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            cct = lldbHelper.recordProcess(executable, proc.pid, fibonacciModule, "computeFibonacci(unsigned long)")
            self.assertEquals(cct.asJson(), '[{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}]')
            self.assertIn("Fibonacci number 3 is 2", proc.stdout.read())
        else:
            warnings.warn("Platform not supported for this test")

    def testBasicRecordingWithThreads(self):
        if platform.system() == "Darwin":
            executable = "testData/fibonacciThread"
            modules = lldbHelper.listModules(executable)
            fibonacciThreadModule = modules[0];
            self.assertIn("fibonacciThread", fibonacciThreadModule)

            cct = lldbHelper.recordCommand(executable, ["3"], fibonacciThreadModule, "computeFibonacci(unsigned long)")
            self.assertEquals(cct.asJson(), '[{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}]')
        else:
            warnings.warn("Platform not supported for this test")

if __name__ == "__main__":
    unittest.main()