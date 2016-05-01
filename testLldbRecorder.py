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

    def testGetModules(self):
        modules = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").getModules()
        self.assertIn("dyld", modules)
        self.assertIn("libc++abi.dylib", modules)
        brokenQuicksortModuleFound = False
        for module in modules:
            if "brokenQuicksort" in module:
                brokenQuicksortModuleFound = True
                break
        self.assertTrue(brokenQuicksortModuleFound)

    def testGetAllFunctions(self):
        functions = lldbRecorder("examples/brokenQuicksort/brokenQuicksort").getAllFunctions()
        self.assertIn("main", functions)
        self.assertIn("swap(int*, int, int)", functions)
        self.assertIn("quicksort(int*, int, int)", functions)
        self.assertIn("fgets", functions)
        self.assertIn("printf", functions)

    def testGetFunctionsInModule(self):
        recorder = lldbRecorder("examples/brokenQuicksort/brokenQuicksort")
        modules = recorder.getModules()
        brokenQuicksortModule = modules[0]
        self.assertIn("brokenQuicksort", brokenQuicksortModule)
        functions = recorder.getFunctionsInModule(brokenQuicksortModule)
        self.assertIn("main", functions)
        self.assertIn("swap(int*, int, int)", functions)
        self.assertIn("quicksort(int*, int, int)", functions)

    def testRecordBadModule(self):
        recorder = lldbRecorder("examples/brokenQuicksort/brokenQuicksort")
        recorder.launchProcess(["1"])
        with self.assertRaises(Exception) as cm:
            cct = recorder.record("ModuleThatDoesNotExist", "main")
        self.assertIn("Unable to find specified module in target.", cm.exception.message)

if __name__ == "__main__":
    if platform.system() != "Darwin":
        warnings.warn("Platform '" + str(platform.system()) + "' may not support the full lldb API")
    unittest.main()
