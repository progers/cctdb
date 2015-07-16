#!/usr/bin/env python

# compare.py - compare calling context trees.

import argparse
import collections
import dtrace
import json
import os.path

def _loadRecording(file):
    if (not os.path.isfile(file)):
        raise Exception('File not found: ' + file)

    with open (file, "r") as inFile:
        data = inFile.read()
    return json.loads(data)

def _stackExistsInCallTree(calls, stack):
    if (len(stack) == 0):
        return True
    if (not calls):
        return False
    for call in calls:
        if (stack[0] == call["name"]):
            if (_stackExistsInCallTree(call["calls"] if "calls" in call else None, stack[1:])):
                return True
    return False

def _findStackDivergences(recordingA, recordingB, currentCalls, callStack = []):
    if (not _stackExistsInCallTree(recordingB, callStack)):
        return [callStack]
    if (not currentCalls):
        return []
    divergences = []
    for call in currentCalls:
        nextCallStack = callStack[:]
        nextCallStack.append(call["name"])
        divergences.extend(_findStackDivergences(recordingA, recordingB, call["calls"] if "calls" in call else None, nextCallStack))
    return divergences

def _printStackDivergenceSummary(recordingA, recordingB):
    divergences = _findStackDivergences(recordingA, recordingB, recordingA)

    lastCalls = []
    for stack in divergences:
        lastCalls.append(stack[-1])
    uniqueLastCalls = set(lastCalls)

    print "Stacks diverged in " + str(len(divergences)) + " places."
    for lastCall in uniqueLastCalls:
        print "    " + lastCall + " (" + str(lastCalls.count(lastCall)) + " instances)"

def _callCount(calls):
    count = len(calls)
    for call in calls:
        if "calls" in call:
            count += _callCount(call["calls"])
    return count

def main():
    parser = argparse.ArgumentParser(description='Compare calling context trees')
    parser.add_argument('recordingA', help='Recording for run A')
    parser.add_argument('recordingB', help='Recording for run B')
    args = parser.parse_args()

    recordingA = _loadRecording(args.recordingA)
    recordingB = _loadRecording(args.recordingB)

    print "Function call count for " + args.recordingA + ": " + str(_callCount(recordingA))
    print "Function call count for " + args.recordingB + ": " + str(_callCount(recordingB))

    print "Differences between " + args.recordingA + " and " + args.recordingB + ":"
    _printStackDivergenceSummary(recordingA, recordingB)

    print "\nDifferences between " + args.recordingB + " and " + args.recordingA + ":"
    _printStackDivergenceSummary(recordingB, recordingA)

if __name__ == "__main__":
    main()