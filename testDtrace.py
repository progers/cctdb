#!/usr/bin/env python

import dtrace
import unittest

class TestDtrace(unittest.TestCase):

    def test_convertStacksToJson(self):
        simple = "foobarbaz"
        expectedSimple = "foobarbaz"
        self.assertEqual(dtrace._convertStacksToJson(simple), expectedSimple)

        simpleOneStack = "fooDTRACE_BEGIN_STACK              bar\nDTRACE_END_STACKbaz"
        expectedSimpleOneStack = "foo[\"bar\"]baz"
        self.assertEqual(dtrace._convertStacksToJson(simpleOneStack), expectedSimpleOneStack)

        complexTwoStacks = "fooDTRACE_BEGIN_STACK              stack1\n              stack2\n              stack3\nDTRACE_END_STACKbazDTRACE_BEGIN_STACK              stacka\n              stackb\n              stackc\nDTRACE_END_STACKbar"
        expectedComplexTwoStacks = "foo[\"stack1\",\"stack2\",\"stack3\"]baz[\"stacka\",\"stackb\",\"stackc\"]bar"
        self.assertEqual(dtrace._convertStacksToJson(complexTwoStacks), expectedComplexTwoStacks)

if __name__ == '__main__':
    unittest.main()