#!/usr/bin/env python

# compare.py - compare calling context trees.

import argparse
import json
import os.path
from cct import CCT, Function

# Return the cases where a subtreeA differs from another tree. In graph theory this is the tree
# embedding problem but to be practical on CCTs, only the following divergences are located:
#    * Divergences where a call stack exists in subtreeA but not otherCCT.
#    * Divergences where Function A with call stack [..., A.parent.parent, A.parent, A] calls
#      Function B N times in subtreeA but less than N times in otherCCT.
#
# Function call order is intentionally ignored because iteration order frequently depends on
# pointers (e.g., iterating over a hash map of pointers to objects).
def _findDivergences(subtree, otherCCT):
    divergences = []
    for call in subtree.calls:
        foundStack, foundStackWithEnoughCalls = _findStack(call.callStack(), otherCCT)

        if not foundStack:
            divergences.append(Divergence(call, "Equivalent stack was not found."))
            continue

        if not foundStackWithEnoughCalls:
            divergences.append(Divergence(call, "Did not find sufficient calls to " + call.name + "."))

        divergences.extend(_findDivergences(call, otherCCT))

    return divergences

# A Function from one CCT that was expected but not found in a second CCT.
class Divergence(object):
    def __init__(self, function, reason):
        self.function = function
        self.reason = reason

# Check for the following relationship between a call stack and a subtree:
#     1) foundStack: Do the function names in the stack appear in the subtree in the correct order?
#     2) foundStackWithEnoughCalls: Let lastCallName be the name of the last function call in the
#        call stack. If lastCallName is called N times by the last call's parent, does the subtree
#        contain at least N calls to lastCallName?
def _findStack(callStack, otherSubtree):
    function = callStack[0]
    if len(callStack) == 1:
        callCountToFunctionName = otherSubtree.callCountToFunctionName(function.name)
        if callCountToFunctionName < 1:
            return False, False
        if callCountToFunctionName < function.parent.callCountToFunctionName(function.name):
            return True, False
        return True, True

    foundStack = False
    foundStackWithEnoughCalls = False
    for otherCall in otherSubtree.calls:
        if function.name != otherCall.name:
            continue
        nextFoundStack, nextFoundStackWithEnoughCalls = _findStack(callStack[1:], otherCall)
        foundStack = foundStack or nextFoundStack
        foundStackWithEnoughCalls = foundStackWithEnoughCalls or nextFoundStackWithEnoughCalls
        if foundStackWithEnoughCalls:
            break
    return foundStack, foundStackWithEnoughCalls

def _loadCCT(file):
    with open (file, 'r') as inFile:
        data = inFile.read()
    return CCT.fromRecord(data)

def _printDivergences(divergences):
    # Destructively group divergences by their last call name and penultimate call name.
    groupedDivergenceMap = {}
    for divergence in divergences:
        key = divergence.function.name
        if divergence.function.parent and divergence.function.parent.name:
            key += divergence.function.parent.name
        if key in groupedDivergenceMap:
            groupedDivergenceMap[key]["count"] += 1
        else:
            groupedDivergenceMap[key] = {}
            groupedDivergenceMap[key]["function"] = divergence.function
            groupedDivergenceMap[key]["count"] = 1

    for groupedDivergence in groupedDivergenceMap.values():
        function = groupedDivergence["function"]
        count = groupedDivergence["count"]
        parent = function.parent
        message = ""
        if parent and parent.name:
            message = "  " + function.name + " which was called by " + parent.name
        else:
            message = "  " + function.name
        if count > 1:
            message += " (" + str(count) + " instances)"
        print message

def _printCCTDivergences(cctA, cctB, aName = 'A', bName = 'B'):
    divergencesAB = _findDivergences(cctA, cctB)
    divergencesBA = _findDivergences(cctB, cctA)

    if len(divergencesAB) == 0 and len(divergencesBA) == 0:
        print "No function call differences were found in the two call trees."
        return

    if len(divergencesAB) > 0:
        print aName + " diverged from " + bName + " in " + str(len(divergencesAB)) + " places:"
        _printDivergences(divergencesAB)
        if len(divergencesBA) > 0:
            print ''

    if len(divergencesBA) > 0:
        print bName + " diverged from " + aName + " in " + str(len(divergencesBA)) + " places:"
        _printDivergences(divergencesBA)

def main():
    parser = argparse.ArgumentParser(description="Compare calling context trees")
    parser.add_argument("recordingA", help="Recording for run A")
    parser.add_argument("recordingB", help="Recording for run B")
    parser.add_argument("-d", "--demangler", help="Demangler")
    args = parser.parse_args()

    cctA = _loadCCT(args.recordingA)
    cctB = _loadCCT(args.recordingB)

    if args.demangler:
        cctA.demangle(args.demangler)
        cctB.demangle(args.demangler)
    else:
        # Try demangling using c++filt but fail silently.
        # MacOS's c++filt version is older and strips underscores by default,
        # which is different from the latest GNU C++filt. Work around this
        # difference by forcing underscores to not be stripped using -n.
        try:
            cctA.demangle("c++filt -n")
            cctB.demangle("c++filt -n")
        except:
            pass

    _printCCTDivergences(cctA, cctB, args.recordingA, args.recordingB)

if __name__ == "__main__":
    main()
