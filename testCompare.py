#!/usr/bin/env python

import compare
import unittest

class TestCompare(unittest.TestCase):

    def _simpleTestTree(self):
        calls = [];
        firstCall = {}
        firstCall["name"] = "fn1()"
        firstCall["calls"] = []
        calls.append(firstCall)
        secondCall = {}
        secondCall["name"] = "fn2()"
        firstCall["calls"].append(secondCall)
        thirdCall = {}
        thirdCall["name"] = "fn3()"
        calls.append(thirdCall)
        return calls # sometimes :/

    def testCallCount(self):
        tree = self._simpleTestTree()
        self.assertEqual(compare._callCount(tree), 3)

    def testStackExistsInCallTree(self):
        tree = self._simpleTestTree()
        self.assertTrue(compare._stackExistsInCallTree(tree, ["fn1()"]))
        self.assertTrue(compare._stackExistsInCallTree(tree, ["fn3()"]))
        self.assertFalse(compare._stackExistsInCallTree(tree, ["fn2()"]))
        self.assertTrue(compare._stackExistsInCallTree(tree, ["fn1()", "fn2()"]))
        self.assertFalse(compare._stackExistsInCallTree(tree, ["fn1()", "fn3()"]))
        self.assertFalse(compare._stackExistsInCallTree(tree, ["fn1()", "fnDNE()"]))

    def testTrivialStackDivergences(self):
        treeA = self._simpleTestTree()
        # Tree does not diverge from itself.
        self.assertEqual(compare._findStackDivergences(treeA, treeA, treeA), [])

        # Empty trees do not diverge.
        self.assertEqual(compare._findStackDivergences([], [], []), [])

    def testSimpleStackDivergences(self):
        treeA = self._simpleTestTree()
        treeB = self._simpleTestTree()
        newCall = {}
        newCall["name"] = "newFn()"
        treeB[0]["calls"][0]["calls"] = [newCall]

        # All calls in A are in B.
        self.assertEqual(compare._findStackDivergences(treeA, treeB, treeA), [])

        # Not all calls in B are in A--newFn is not in A.
        self.assertEqual(compare._findStackDivergences(treeB, treeA, treeB), [['fn1()', 'fn2()', 'newFn()']])

    #def testDuplicateCallCountDivergences(self):
    #    treeA = self._simpleTestTree()
    #    treeB = self._simpleTestTree()
    #    secondFunctionAgain = {}
    #    secondFunctionAgain["name"] = "fn2()"
    #    treeB[0]["calls"].append(secondFunctionAgain)

    #    # All calls in A are in B.
    #    self.assertEqual(compare._findStackDivergences(treeA, treeB, treeA), [])

    #    # Not all calls in B are in A--there are two fn1->fn2's in B but only one in A.
    #    self.assertEqual(compare._findStackDivergences(treeB, treeA, treeB), [['fn1()', 'fn2()']])


    #def testSubtreeConsistency(self):
    #    # Tree where fn2 and fn3 are both called from fn1.
    #    treeA = [];
    #    aFirstCall = {}
    #    aFirstCall["name"] = "fn1()"
    #    aFirstCall["calls"] = []
    #    treeA.append(aFirstCall)
    #    aSecondCall = {}
    #    aSecondCall["name"] = "fn2()"
    #    aFirstCall["calls"].append(aSecondCall)
    #    aThirdCall = {}
    #    aThirdCall["name"] = "fn3()"
    #    aFirstCall["calls"].append(aThirdCall)

    #    # Tree where fn1 is called twice. The first call to fn1 calls fn2. The second call to fn1 calls fn3.
    #    treeB = [];
    #    bFirstCall = {}
    #    bFirstCall["name"] = "fn1()"
    #    treeB.append(bFirstCall)
    #    bSecondCall = {}
    #    bSecondCall["name"] = "fn2()"
    #    bFirstCall["calls"] = [bSecondCall]
    #    bThirdCall = {}
    #    bThirdCall["name"] = "fn1()"
    #    treeB.append(bThirdCall)
    #    bFourthCall = {}
    #    bFourthCall["name"] = "fn3()"
    #    bThirdCall["calls"] = [bFourthCall]

    #    self.assertNotEqual(compare._findStackDivergences(treeA, treeB, treeA), [])
    #    self.assertNotEqual(compare._findStackDivergences(treeB, treeA, treeB), [])

if __name__ == '__main__':
    unittest.main()