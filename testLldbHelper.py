#!/usr/bin/env python

import lldbHelper
import platform
import warnings
import unittest

class TestLldbHelper(unittest.TestCase):

    def testBrokenExecutable(self):
        with self.assertRaises(Exception) as cm:
            lldbHelper.listModules("does/not/exist")
        self.assertEqual(cm.exception.message, "Error creating target 'does/not/exist'")

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

if __name__ == "__main__":
    unittest.main()