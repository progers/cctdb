#!/usr/bin/env python

# compare.py - compare calling context trees.

import argparse
import collections
from collections import defaultdict
import dtrace
import json
import os.path

# Given two trees, return the lists of function names where one tree diverges from the other.
# In graph theory, this is essentially the tree embedding problem. To be practical on call trees,
# some assumptions have been made that seem to be reasonable on real datasets:
#   * Ordering is ignored. When iterating over a hashtable of pointers, this lets us ignore the
#     difference in call order at the cost of missing some tree differences.
#   * The number of calls to a function is only lightly enforced.
#     In the following example, we only report that A diverges from B but B does not diverge from A:
#         tree A: fn1() calls [fn2(), fn2(), fn2()]
#         tree B: fn1() calls [fn2()]
# TODO(philip): This is hard to understand and needs better naming and comments.
def _findTreeDivergences(tree, otherTree):
    return _findDivergences([tree], otherTree)

def _findDivergences(currentCallList, otherTree):
    matchType = _hasMatchingCallList(currentCallList, [otherTree])
    if (matchType == CallListMatchType.NOMATCH):
        return [_callNameListFromCallList(currentCallList)]

    divergences = []
    if (matchType == CallListMatchType.MATCHONLYCALLS):
        divergences.append(_callNameListFromCallList(currentCallList))

    currentCall = currentCallList[-1]
    if ("calls" in currentCall):
        for call in currentCall["calls"]:
            nextCallList = []
            nextCallList.extend(currentCallList)
            nextCallList.append(call)
            divergences.extend(_findDivergences(nextCallList, otherTree))

    return divergences

def _callNameListFromCallList(callList):
    names = []
    for call in callList:
        names.append(call["name"])
    return names

class CallListMatchType:
    NOMATCH = 1
    MATCHONLYCALLS = 2
    MATCH = 3

def _countCallsToFunction(call, name):
    if ("cachedCountMap" in call):
        return call["cachedCountMap"][name]
    counts = defaultdict(int)
    for c in call["calls"]:
        counts[c["name"]] += 1
    call["cachedCountMap"] = counts
    return counts[name]

# Check if a call list exists in a subtree. To find matches in a tree, [tree] can be passed as the
# partialCallList.
# This function returns MATCHONLYCALLS if a the sequence in matchingCallList appears in the subtree.
# This function returns MATCH if MATCHONLYCALLS AND the call counts of each of the calls in
# matchingCallList exceeds the corresponding counts in the subtree.
# Otherwise, NOMATCH is returned.
# TODO(philip): This is hard to understand and needs better naming and comments.
def _hasMatchingCallList(matchingCallList, partialCallList):
    partialCallListSize = len(partialCallList)
    matchingCallListSize = len(matchingCallList)
    if (matchingCallListSize == 0):
        return CallListMatchType.NOMATCH
    # Tree roots are always equal.
    if (partialCallListSize == 1 and matchingCallListSize == 1):
        return CallListMatchType.MATCH

    lastCall = partialCallList[-1]
    nextMatchingCall = matchingCallList[partialCallListSize]
    foundMatchOnlyCalls = False
    if ("calls" in lastCall):
        for nextCall in lastCall["calls"]:
            if (nextCall["name"] == nextMatchingCall["name"]):
                if (partialCallListSize + 1 == matchingCallListSize):
                    nextCallSiblingCount = _countCallsToFunction(lastCall, nextCall["name"])
                    nextMatchingCallSiblingCount = _countCallsToFunction(matchingCallList[partialCallListSize - 1], nextCall["name"])
                    if (nextCallSiblingCount >= nextMatchingCallSiblingCount):
                        return CallListMatchType.MATCH
                    foundMatchOnlyCalls = True
                else:
                    nextPartialCallList = []
                    nextPartialCallList.extend(partialCallList)
                    nextPartialCallList.append(nextCall)
                    nextMatch = _hasMatchingCallList(matchingCallList, nextPartialCallList)
                    if (nextMatch == CallListMatchType.MATCH):
                        return CallListMatchType.MATCH
                    if (nextMatch == CallListMatchType.MATCHONLYCALLS):
                        foundMatchOnlyCalls = True
    if (foundMatchOnlyCalls):
        return CallListMatchType.MATCHONLYCALLS
    return CallListMatchType.NOMATCH

def _loadRecording(file):
    if (not os.path.isfile(file)):
        raise Exception('File not found: ' + file)

    with open (file, "r") as inFile:
        data = inFile.read()
    return json.loads(data)

def _printTreeDivergenceSummary(recordingA, recordingB):
    divergences = _findTreeDivergences(recordingA, recordingB)

    lastCalls = []
    for stack in divergences:
        lastCalls.append(stack[-1])
    uniqueLastCalls = set(lastCalls)

    print "Trees diverged in " + str(len(divergences)) + " places."
    for lastCall in uniqueLastCalls:
        print "    " + lastCall + " (" + str(lastCalls.count(lastCall)) + " instances)"

def _callCount(subtree):
    count = len(subtree["calls"])
    for call in subtree["calls"]:
        if "calls" in call:
            count += _callCount(call)
    return count

def main():
    parser = argparse.ArgumentParser(description='Compare calling context trees')
    parser.add_argument('recordingA', help='Recording for run A')
    parser.add_argument('recordingB', help='Recording for run B')
    args = parser.parse_args()

    recordingA = _loadRecording(args.recordingA)
    recordingB = _loadRecording(args.recordingB)

    # Multiple subtrees can occur if there are multiple entry points into a program or if the user
    # filtered on a specific function call. Root both recordings at a synthetic call to 'begin'.
    rootA = {}
    rootA["name"] = "begin"
    rootA["calls"] = recordingA[:]
    recordingA = rootA
    rootB = {}
    rootB["name"] = "begin"
    rootB["calls"] = recordingB[:]
    recordingB = rootB

    print "Function call count for " + args.recordingA + ": " + str(_callCount(recordingA))
    print "Function call count for " + args.recordingB + ": " + str(_callCount(recordingB))

    print "Differences between " + args.recordingA + " and " + args.recordingB + ":"
    _printTreeDivergenceSummary(recordingA, recordingB)

    print "\nDifferences between " + args.recordingB + " and " + args.recordingA + ":"
    _printTreeDivergenceSummary(recordingB, recordingA)

if __name__ == "__main__":
    main()