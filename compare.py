#!/usr/bin/env python

# compare.py - compare calling context trees.

import argparse
import collections
import dtrace
import json
import os.path

# Given two trees, return the lists of function names where one tree diverges from the other.
# In graph theory, this is essentially the tree embedding problem. To be practical on call trees,
# some assumptions are made:
#   TODO: DESCRIBE THESE.
def _findTreeDivergences(tree, otherTree):
    return _findDivergences([tree], otherTree)

def _findDivergences(currentCallList, otherTree):
    if (not _hasMatchingCallList(currentCallList, [otherTree])):
        return [_callNameListFromCallList(currentCallList)]

    divergences = []
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

# True if a call list exists where function names match for every frame. partialCallList has calls
# known to match so far. To find matches in a tree, [tree] can be passed as the partialCallList.
def _hasMatchingCallList(matchingCallList, partialCallList):
    partialCallListSize = len(partialCallList)
    matchingCallListSize = len(matchingCallList)
    if (matchingCallListSize == 0):
        return False
    if (partialCallListSize == matchingCallListSize):
        return True

    lastCall = partialCallList[-1]
    nextMatchingCall = matchingCallList[partialCallListSize]
    if ("calls" in lastCall):
        for nextCall in lastCall["calls"]:
            if (nextCall["name"] == nextMatchingCall["name"]):
                nextPartialCallList = []
                nextPartialCallList.extend(partialCallList)
                nextPartialCallList.append(nextCall)
                if (partialCallListSize + 1 == matchingCallListSize):
                    return True
                if (_hasMatchingCallList(matchingCallList, nextPartialCallList)):
                    return True
    return False

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