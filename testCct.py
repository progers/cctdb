#!/usr/bin/env python

from cct import CCT, Function
import unittest

class TestCCT(unittest.TestCase):

    def _simpleCCT(self):
        cct = CCT()
        fn1 = Function("fn1")
        fn2 = Function("fn2")
        fn3 = Function("fn3")
        cct.addCall(fn1)
        cct.addCall(fn2)
        fn1.addCall(fn3)
        return cct

    def testConstruction(self):
        cct = CCT()

    def testReparenting(self):
        cct = self._simpleCCT()
        fn1 = cct.calls[0]
        fn2 = cct.calls[1]
        fn3 = fn1.calls[0]
        with self.assertRaises(ValueError):
            fn2.addCall(fn3)
        with self.assertRaises(ValueError):
            fn1.addCall(cct)
        fn4 = Function("fn4")
        fn2.addCall(fn4)

    def testCallStack(self):
        cct = self._simpleCCT()
        fn1 = cct.calls[0]
        fn2 = cct.calls[1]
        fn3 = fn1.calls[0]
        self.assertEquals(cct.callStack(), [])
        self.assertEquals(fn1.callStack(), [fn1])
        self.assertEquals(fn2.callStack(), [fn2])
        self.assertEquals(fn3.callStack(), [fn1, fn3])
        fn4 = Function("fn4")
        self.assertEquals(fn4.callStack(), [fn4])
        fn3.addCall(fn4)
        self.assertEquals(fn4.callStack(), [fn1, fn3, fn4])

    def testCallNameStack(self):
        cct = self._simpleCCT()
        fn1 = cct.calls[0]
        fn2 = cct.calls[1]
        fn3 = fn1.calls[0]
        self.assertEquals(cct.callNameStack(), [])
        self.assertEquals(fn1.callNameStack(), ["fn1"])
        self.assertEquals(fn2.callNameStack(), ["fn2"])
        self.assertEquals(fn3.callNameStack(), ["fn1", "fn3"])
        fn4 = Function("fn4")
        self.assertEquals(fn4.callNameStack(), ["fn4"])
        fn3.addCall(fn4)
        self.assertEquals(fn4.callNameStack(), ["fn1", "fn3", "fn4"])

    def testCallCountToFunctionName(self):
        cct = self._simpleCCT()
        self.assertEquals(cct.callCountToFunctionName("fn1"), 1)
        self.assertEquals(cct.callCountToFunctionName("fn2"), 1)
        self.assertEquals(cct.callCountToFunctionName("fn3"), 0)
        self.assertEquals(cct.callCountToFunctionName(""), 0)
        self.assertEquals(cct.callCountToFunctionName("son, why you never call?"), 0)
        fn1 = cct.calls[0]
        self.assertEquals(fn1.callCountToFunctionName("fn3"), 1)
        secondFn3 = Function("fn3")
        fn1.addCall(secondFn3)
        self.assertEquals(fn1.callCountToFunctionName("fn3"), 2)

    def testUniqueCallNames(self):
        cct = self._simpleCCT()
        self.assertEquals(cct.uniqueCallNames(), ["fn2", "fn1"])
        secondFn2 = Function("fn2")
        cct.addCall(secondFn2)
        self.assertEquals(cct.uniqueCallNames(), ["fn2", "fn1"])

    def testJsonEncoding(self):
        cct = self._simpleCCT()
        fn1 = cct.calls[0]
        self.assertEquals(fn1.asJson(), '{"name": "fn1", "calls": [{"name": "fn3"}]}')
        self.assertEquals(fn1.asJson(2), '{\n  "name": "fn1", \n  "calls": [\n    {\n      "name": "fn3"\n    }\n  ]\n}')
        self.assertEquals(cct.asJson(), '[{"name": "fn1", "calls": [{"name": "fn3"}]}, {"name": "fn2"}]')

    def testJsonDecoding(self):
        cct = self._simpleCCT()
        fn1 = cct.calls[0]
        self.assertEquals(fn1.fromJson(fn1.asJson()).asJson(), fn1.asJson())
        self.assertEquals(cct.fromJson(cct.asJson()).asJson(), cct.asJson())

if __name__ == "__main__":
    unittest.main()
