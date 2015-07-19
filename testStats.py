#!/usr/bin/env python

from cct import CCT, Function
from collections import defaultdict
import stats
import unittest

class TestStats(unittest.TestCase):

    def _simpleCCT(self):
        cct = CCT()
        fn1 = Function("fn1")
        fn2 = Function("fn2")
        fn3 = Function("fn3")
        cct.addCall(fn1)
        cct.addCall(fn2)
        fn1.addCall(fn3)
        return cct

    def testCountFunctionCallNames(self):
        cct = self._simpleCCT()
        cct.addCall(Function("fn1"))

        functionNamesCount = defaultdict(int)
        stats._countFunctionCallNames(cct, functionNamesCount)
        self.assertEquals(len(functionNamesCount), 3)
        self.assertEquals(functionNamesCount["fn1"], 2)
        self.assertEquals(functionNamesCount["fn2"], 1)
        self.assertEquals(functionNamesCount["fn3"], 1)

    def testTopCalledFunctionCallNames(self):
        cct = self._simpleCCT()
        cct.addCall(Function("fn1"))

        # Check results when count > |calls in tree|.
        topCalls = stats._topCalledFunctionCallNames(cct, 5)
        self.assertEquals(len(topCalls), 3)
        self.assertEquals(topCalls[0], (2, "fn1"))
        self.assertEquals(topCalls[1], (1, "fn3"))
        self.assertEquals(topCalls[2], (1, "fn2"))

        # Check results when count < |calls in tree|.
        topCalls = stats._topCalledFunctionCallNames(cct, 2)
        self.assertEquals(len(topCalls), 2)
        self.assertEquals(topCalls[0], (2, "fn1"))
        self.assertEquals(topCalls[1], (1, "fn3"))

if __name__ == "__main__":
    unittest.main()