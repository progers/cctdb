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

    def _simpleRootedTestTree(self):
        tree = {}
        tree["name"] = "begin"
        tree["calls"] = self._simpleTestTree()
        return tree

    def testCallCount(self):
        tree = self._simpleRootedTestTree()
        self.assertEqual(compare._callCount(tree), 3)

    def testHasMatchingCallList(self):
        tree = self._simpleRootedTestTree()

        # Empty call list has no matches.
        self.assertFalse(compare._hasMatchingCallList([], [tree]))

        self.assertTrue(compare._hasMatchingCallList([tree], [tree]))
        self.assertTrue(compare._hasMatchingCallList([tree, tree["calls"][0]], [tree]))
        self.assertTrue(compare._hasMatchingCallList([tree, tree["calls"][0], tree["calls"][0]["calls"][0]], [tree]))

        # Test a call list that doesn't exist.
        self.assertFalse(compare._hasMatchingCallList([tree, tree["calls"][0], tree["calls"][0]["calls"][0], tree["calls"][0]], [tree]))

    def testTrivialTreeDivergences(self):
        tree = self._simpleRootedTestTree()
        # Tree does not diverge from itself.
        self.assertEqual(compare._findTreeDivergences(tree, tree), [])

    def testSimpleTreeDivergences(self):
        treeA = self._simpleRootedTestTree()
        treeB = self._simpleRootedTestTree()
        newCall = {}
        newCall["name"] = "newFn()"
        treeB["calls"][0]["calls"][0]["calls"] = [newCall]

        # All calls in A are in B.
        divergences = compare._findTreeDivergences(treeA, treeB)
        self.assertEqual(len(divergences), 0)

        # Not all calls in B are in A--newFn is not in A.
        divergences = compare._findTreeDivergences(treeB, treeA)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0], ['begin', 'fn1()', 'fn2()', 'newFn()'])

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