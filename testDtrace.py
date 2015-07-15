#!/usr/bin/env python

import dtrace
import unittest

class TestDtrace(unittest.TestCase):

    def testConvertStacksToJson(self):
        self.assertEqual(dtrace._convertStacksToJson("foobarbaz"), "foobarbaz")

        simpleOneStack = "fooDTRACE_BEGIN_STACK              bar\nDTRACE_END_STACKbaz"
        self.assertEqual(dtrace._convertStacksToJson(simpleOneStack), "foo[\"bar\"]baz")

    def testParsingStacksToJson(self):
        complexTwoStacks = "fooDTRACE_BEGIN_STACK              stack1\n              stack2\n              stack3\nDTRACE_END_STACKbazDTRACE_BEGIN_STACK              stacka\n              stackb\n              stackc\nDTRACE_END_STACKbar"
        self.assertEqual(dtrace._convertStacksToJson(complexTwoStacks), "foo[\"stack1\",\"stack2\",\"stack3\"]baz[\"stacka\",\"stackb\",\"stackc\"]bar")

    def testParsingStackWithModuleAndOffsetToJson(self):
        stackWithModuleAndOffset = "fooDTRACE_BEGIN_STACK              modulename`bar+0x1111\nDTRACE_END_STACKbaz"
        self.assertEqual(dtrace._convertStacksToJson(stackWithModuleAndOffset), "foo[\"modulename`bar\"]baz")

    def testTrivialCallTreeGeneration(self):
        recording = """
        [
            {"type": "function", "name": "ignored", "timestamp": 1, "stack": DTRACE_BEGIN_STACK
                          module`a()
            DTRACE_END_STACK}
        ]
        """
        tree = dtrace._convertRecordingToCallTree(recording)
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["name"], "module`a()")
        self.assertEqual(len(tree[0]["calls"]), 0)

    def testSimpleCallTreeGeneration(self):
        recording = """
        [
            {"type": "function", "name": "ignored", "timestamp": 1, "stack": DTRACE_BEGIN_STACK
                          module`a()
                          module`b()
            DTRACE_END_STACK},
            {"type": "function", "name": "ignored", "timestamp": 2, "stack": DTRACE_BEGIN_STACK
                          module`c()
                          module`a()
                          module`b()
            DTRACE_END_STACK}
        ]
        """
        tree = dtrace._convertRecordingToCallTree(recording)
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["name"], "module`a()")
        self.assertEqual(len(tree[0]["calls"]), 1)
        self.assertEqual(len(tree[0]["calls"]), 1)
        self.assertEqual(tree[0]["calls"][0]["name"], "module`c()")
        self.assertEqual(len(tree[0]["calls"][0]["calls"]), 0)

    def testDegenerateCallTreeGeneration(self):
        recording = """
        [
            {"type": "function", "name": "ignored", "timestamp": 1, "stack": DTRACE_BEGIN_STACK
            DTRACE_END_STACK},
            {"type": "function", "name": "ignored", "timestamp": 2, "stack": DTRACE_BEGIN_STACK
                          module`aa()
                          module`bb()
                          module`cc()
            DTRACE_END_STACK},
            {"type": "function", "name": "ignored", "timestamp": 3, "stack": DTRACE_BEGIN_STACK
            DTRACE_END_STACK},
            {"type": "function", "name": "ignored", "timestamp": 2, "stack": DTRACE_BEGIN_STACK
                          module`qq()
                          module`qq()
                          module`aa()
            DTRACE_END_STACK},
            {"type": "function", "name": "ignored", "timestamp": 3, "stack": DTRACE_BEGIN_STACK
            DTRACE_END_STACK}
        ]
        """
        tree = dtrace._convertRecordingToCallTree(recording)
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]["name"], "module`aa()")
        self.assertEqual(len(tree[0]["calls"]), 0)
        self.assertEqual(tree[1]["name"], "module`qq()")
        self.assertEqual(len(tree[1]["calls"]), 0)

if __name__ == '__main__':
    unittest.main()