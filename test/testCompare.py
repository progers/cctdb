from cct import CCT, Function
import compare
import unittest

class TestCompare(unittest.TestCase):

    def _simpleCCT(self):
        cct = CCT()
        fn1 = Function("fn1")
        fn2 = Function("fn2")
        fn3 = Function("fn3")
        cct.addCall(fn1)
        cct.addCall(fn2)
        fn1.addCall(fn3)
        return cct

    def testFindStack(self):
        cct = self._simpleCCT()
        cctOther = self._simpleCCT()

        fn1 = cct.calls[0]
        foundStack, foundStackWithEnoughCalls = compare._findStack(fn1.callStack(), cctOther)
        self.assertTrue(foundStack)
        self.assertTrue(foundStackWithEnoughCalls)

        fn3 = fn1.calls[0]
        foundStack, foundStackWithEnoughCalls = compare._findStack(fn3.callStack(), cctOther)
        self.assertTrue(foundStack)
        self.assertTrue(foundStackWithEnoughCalls)

        fn4 = Function("fn4")
        foundStack, foundStackWithEnoughCalls = compare._findStack(fn4.callStack(), cctOther)
        self.assertFalse(foundStack)
        self.assertFalse(foundStackWithEnoughCalls)
        foundStack, foundStackWithEnoughCalls = compare._findStack(fn4.callStack(), cct)
        self.assertFalse(foundStack)
        self.assertFalse(foundStackWithEnoughCalls)

        fn3.addCall(fn4)
        foundStack, foundStackWithEnoughCalls = compare._findStack(fn4.callStack(), cctOther)
        self.assertFalse(foundStack)
        self.assertFalse(foundStackWithEnoughCalls)
        foundStack, foundStackWithEnoughCalls = compare._findStack(fn4.callStack(), cct)
        self.assertTrue(foundStack)
        self.assertTrue(foundStackWithEnoughCalls)

    def testSimpleTreeDivergence(self):
        cctA = self._simpleCCT()
        cctB = self._simpleCCT()
        newFn = Function("newFn")
        cctB.calls[0].calls[0].addCall(newFn)

        # Trees do not diverge from themselves.
        self.assertEqual(compare._findDivergences(cctA, cctA), [])
        self.assertEqual(compare._findDivergences(cctB, cctB), [])

        # All calls in A are in B.
        self.assertEqual(compare._findDivergences(cctA, cctB), [])

        # Not all calls in B are in A--newFn is not in A.
        divergences = compare._findDivergences(cctB, cctA)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].function, newFn)
        self.assertEqual(divergences[0].reason, "Equivalent stack was not found.")

    def testDuplicateDivergence(self):
        cctA = self._simpleCCT()
        cctB = self._simpleCCT()
        fn1 = cctB.calls[0]
        fn3 = cctB.calls[0].calls[0]
        fn3Again = Function("fn3")
        fn1.addCall(fn3Again)

        # All calls in A are in B.
        self.assertEqual(compare._findDivergences(cctA, cctB), [])

        # Not all calls in B are in A--there are two fn1->fn3's in B but only one in A.
        divergences = compare._findDivergences(cctB, cctA)
        self.assertEqual(len(divergences), 2)
        self.assertEqual(divergences[0].function, fn3)
        self.assertEqual(divergences[0].reason, "Did not find sufficient calls to fn3.")
        self.assertEqual(divergences[1].function, fn3Again)
        self.assertEqual(divergences[1].reason, "Did not find sufficient calls to fn3.")

    def testStructuralDivergence(self):
        # Tree where fn2 and fn3 are both called from fn1.
        cctA = CCT()
        fn1 = Function("fn1")
        fn2 = Function("fn2")
        fn3 = Function("fn3")
        fn1.addCall(fn2)
        fn1.addCall(fn3)
        cctA.addCall(fn1)

        # Tree where fn1 is called twice. The first call to fn1 calls fn2. The second call to fn1 calls fn3.
        cctB = CCT()
        firstFn1 = Function("fn1")
        secondFn1 = Function("fn1")
        fn2 = Function("fn2")
        fn3 = Function("fn3")
        firstFn1.addCall(fn2)
        secondFn1.addCall(fn3)
        cctB.addCall(firstFn1)
        cctB.addCall(secondFn1)

        self.assertEqual(compare._findDivergences(cctA, cctB), [])

        divergences = compare._findDivergences(cctB, cctA)
        self.assertEqual(len(divergences), 2)
        self.assertEqual(divergences[0].function, firstFn1)
        self.assertEqual(divergences[0].reason, "Did not find sufficient calls to fn1.")
        self.assertEqual(divergences[1].function, secondFn1)
        self.assertEqual(divergences[1].reason, "Did not find sufficient calls to fn1.")

        # Add a stack divergence below the count divergence found above.
        newFn = Function("newFn")
        firstFn1.addCall(newFn)
        self.assertEqual(compare._findDivergences(cctA, cctB), [])
        divergences = compare._findDivergences(cctB, cctA)
        self.assertEqual(len(divergences), 3)
        self.assertEqual(divergences[0].function, firstFn1)
        self.assertEqual(divergences[0].reason, "Did not find sufficient calls to fn1.")
        self.assertEqual(divergences[1].function, newFn)
        self.assertEqual(divergences[1].reason, "Equivalent stack was not found.")
        self.assertEqual(divergences[2].function, secondFn1)
        self.assertEqual(divergences[2].reason, "Did not find sufficient calls to fn1.")

    def testOutOfOrderIteration(self):
        # Pointers are used for iteration (e.g., iterating over a hashmap keyed on pointers) and the
        # divergence algorithm needs to ignore this ordering.

        # Tree where fn1 is called twice, separated by some other call. The first fn1 calls fn3. The
        # second fn1 calls both fn3 and fn4.
        cctA = CCT()
        firstFn1 = Function("fn1")
        firstFn1.addCall(Function("fn3"))
        secondFn1 = Function("fn1")
        secondFn1.addCall(Function("fn3"))
        secondFn1.addCall(Function("fn4"))
        cctA.addCall(firstFn1)
        cctA.addCall(Function("fn2"))
        cctA.addCall(secondFn1)

        # Tree where fn1 is called twice, separated by some other call. The first fn1 calls fn3 and
        # fn4. The second fn1 calls just fn3.
        cctB = CCT()
        firstFn1 = Function("fn1")
        firstFn1.addCall(Function("fn3"))
        firstFn1.addCall(Function("fn4"))
        secondFn1 = Function("fn1")
        secondFn1.addCall(Function("fn3"))
        cctB.addCall(firstFn1)
        cctB.addCall(Function("fn2"))
        cctB.addCall(secondFn1)

        # All calls in A are in B and vice versa.
        self.assertEqual(compare._findDivergences(cctA, cctB), [])
        self.assertEqual(compare._findDivergences(cctB, cctA), [])

        # Add a divergence and ensure it is found.
        fn5 = Function("fn5")
        firstFn1.calls[0].addCall(fn5)
        self.assertEqual(compare._findDivergences(cctA, cctB), [])
        divergences = compare._findDivergences(cctB, cctA)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].reason, "Equivalent stack was not found.")
        self.assertEqual(divergences[0].function, fn5)

if __name__ == "__main__":
    unittest.main()
