#!/usr/bin/env python

# LLDB is not on the python path by default. Try to give a helpful error message if it isn't found.
try:
    import lldb
except ImportError:
    print "LLDB not found in PYTHONPATH. Run the following command to add it:"
    print "  export PYTHONPATH=/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python"
    raise Exception("Couldn't locate the 'lldb' module, please set PYTHONPATH correctly")

from cct import CCT, Function
import gc
import os
from record import record
import unittest
import warnings

# Convenience class for launching an executable and recording a CCT.
#
# The LLDB python interface will segfault on teardown if the teardown process is not controlled.
# ("Python quit unexpectedly while using the _lldb.so plugin.", EXC_BAD_ACCESS (SIGSEGV))
# See: https://llvm.org/bugs/show_bug.cgi?id=27639
#
# To workaround this, we use a class that cleans itself up on destruction. We hold on to
# these TestRecorder objects until the end of all test runs, then destroy them in cleanupRecorders.
# This teardown approach is based on lldb's python api test suite in TestBase.tearDown from
# .../packages/Python/lldbsuite/test/lldbtest.py
class TestRecorder:
    activeRecorders = []

    def __init__(self, executable, launchArgs, breakpointFunctionName):
        TestRecorder.activeRecorders.append(self)
        self._cct = None

        self._target = lldb.SBDebugger.Create().CreateTarget(executable)
        if not self._target:
            raise Exception("Could not create target '" + executable + "'")
        self._target.GetDebugger().SetAsync(False)
        
        # Set a breakpoint before launching.
        self._target.BreakpointCreateByName(breakpointFunctionName)
        if self._target.num_breakpoints <= 0:
            raise Exception("Failed to create function breakpoint.")

        # Launch the process.
        process = self._target.LaunchSimple(launchArgs, None, os.getcwd())
        if not process:
            raise Exception("Could not launch '" + executable + "' with args '" + ",".join(launchArgs) + "'")

        # Ensure that a breakpoint is active.
        for breakpoint in self._target.breakpoint_iter():
            if breakpoint.GetNumLocations() <= 0:
                raise Exception("Could not break on function. Check the specified function name.")

    def record(self, shouldStayWithinModule = True):
        return record(self._target, shouldStayWithinModule)

    def continueProcess(self):
        self._target.GetProcess().Continue()

    def __del__(self):
        if self._target and self._target.GetDebugger():
            # Must manually clean up, see: https://llvm.org/bugs/show_bug.cgi?id=27639.
            self._target.GetDebugger().DeleteTarget(self._target)
            self._target.GetDebugger().Terminate()

    @staticmethod
    def cleanupRecorders():
        # Ensure all the references to SB objects have gone away so that we can be sure that all
        # test-specific resources have been freed before we attempt to delete the targets.
        gc.collect()

        # Delete the target(s) from the debugger as a general cleanup step. This includes
        # terminating the process for each target.
        for recorder in TestRecorder.activeRecorders:
            target = recorder._target
            if target:
                process = target.GetProcess()
                if process:
                    process.Kill()
        TestRecorder.activeRecorders = []

class TestRecord(unittest.TestCase):
    # (See comment above TestRecorder for why this is needed.)
    @classmethod
    def tearDownClass(self):
        TestRecorder.cleanupRecorders()

    def testBasicRecordingAtMain(self):
        cct = TestRecorder("testData/quicksort", ["1"], "main").record()
        self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)"}]}]}]')

    def testBasicRecordingAtSubroutine(self):
        sortCct = TestRecorder("testData/quicksort", ["1", "3", "2"], "sort(int*, int)").record()
        self.assertEquals(sortCct.asJson(), '[{"name": "sort(int*, int)", "calls": [{"name": "quicksort(int*, int, int)", "calls": [{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}, {"name": "quicksort(int*, int, int)"}, {"name": "quicksort(int*, int, int)"}]}]}]')

        partitionCct = TestRecorder("testData/quicksort", ["1", "3", "2"], "partition(int*, int, int)").record()
        self.assertEquals(partitionCct.asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')

        swapCct = TestRecorder("testData/quicksort", ["1", "3", "2"], "swap(int*, int, int)").record()
        self.assertEquals(swapCct.asJson(), '[{"name": "swap(int*, int, int)"}]')

    def testMultipleBreakpoints(self):
        recorder = TestRecorder("testData/quicksort", ["3", "1", "2", "3", "2"], "partition(int*, int, int)")
        self.assertEquals(recorder.record().asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')
        recorder.continueProcess()
        self.assertEquals(recorder.record().asJson(), '[{"name": "partition(int*, int, int)", "calls": [{"name": "swap(int*, int, int)"}]}]')
        recorder.continueProcess()
        self.assertEquals(recorder.record().asJson(), '[{"name": "partition(int*, int, int)"}]')

    def testRecordStaysInSpecifiedLibrary(self):
        cct = TestRecorder("testData/dynamicLoaderDarwin", [], "main").record()
        # Ensure no DynamicClassDarwin calls are in the tree.
        self.assertEquals(cct.asJson(), '[{"name": "main", "calls": [{"name": "notDynamicC()"}]}]')

    def testRecordDoesNotStayInSpecifiedLibrary(self):
        cct = TestRecorder("testData/dynamicLoaderDarwin", [], "main").record(False)
        self.assertIn("DynamicClassDarwin", cct.asJson())

    @unittest.skip("FIXME(phil): support thread stepping in.")
    def testRecordingWithThreads(self):
        recorder = TestRecorder("testData/fibonacciThread", ["3"], "computeFibonacci(unsigned long)")
        firstCall = recorder.record()
        self.assertEquals(firstCall.asJson(), '[{"name": "computeFibonacci(unsigned long)", "calls": [{"name": "fib(unsigned long)", "calls": [{"name": "fib(unsigned long)"}, {"name": "fib(unsigned long)"}]}]}]')
        
        # Each call to computeFibonacci should have the same subtree.
        recorder.continueProcess()
        secondCall = recorder.record()
        self.assertEquals(firstCall.asJson(), secondCall.asJson())
        recorder.continueProcess()
        thirdCall = recorder.record()
        self.assertEquals(firstCall.asJson(), thirdCall.asJson())

    # Not supported! See comment in recorder.py, recordSubtreeCalls.
    # This test checks for assertions and that that recording works as if new threads never existed.
    def testRecordingIntoNewThreads(self):
        cct = TestRecorder("testData/fibonacciThread", ["3"], "main").record()
        self.assertEquals(cct.asJson(), '[{"name": "main"}]')

    def testComplexInlinedTree(self):
        recorder = TestRecorder("testData/complexInlinedTree", [], "A(int&)")

        firstBranch = recorder.record()
        self.assertEquals(firstBranch.asJson(), '[{"name": "A(int&)", "calls": [{"name": "C(int&)", "calls": [{"name": "A(int&)", "calls": [{"name": "A(int&)"}]}]}]}]')

        recorder.continueProcess()
        secondBranch = recorder.record()
        self.assertEquals(secondBranch.asJson(), '[{"name": "A(int&)"}]')

    def testComplexInlinedTreeWithDeepBreakpoint(self):
        cct = TestRecorder("testData/complexInlinedTree", [], "C(int&)").record()
        self.assertEquals(cct.asJson(), '[{"name": "C(int&)", "calls": [{"name": "A(int&)", "calls": [{"name": "A(int&)"}]}]}]')

    def testComplexInlinedCases(self):
        recorder = TestRecorder("testData/complexInlinedCases", [], "A(int&)")

        branch0 = recorder.record()
        self.assertEquals(branch0.asJson(), '[{"name": "A(int&)", "calls": [{"name": "C(int&)"}]}]')

        recorder.continueProcess()
        branch1 = recorder.record()
        self.assertEquals(branch1.asJson(), '[{"name": "A(int&)"}]')

        recorder.continueProcess()
        branch3 = recorder.record()
        self.assertEquals(branch3.asJson(), '[{"name": "A(int&)"}]')

    def testSingleInstructionInline(self):
        cct = TestRecorder("testData/singleInstructionInline", [], "A()").record()
        self.assertEquals(cct.asJson(), '[{"name": "A()", "calls": [{"name": "C()", "calls": [{"name": "D()"}]}]}]')

    def testOptimizationWarning(self):
        with warnings.catch_warnings(record=True) as w:
            cct = TestRecorder("testData/optimizedQuicksort", ["1"], "main").record()
            self.assertIn("was compiled with optimizations which can cause stepping issues", str(w[0].message))

if __name__ == "__main__":
    unittest.main()
