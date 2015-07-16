#!/usr/bin/env python

# compare.py - compare the calling context trees of two runs.

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

def _stackExistsInCalls(calls, stack):
    if (len(stack) == 0):
        return True
    if (not calls):
        return False
    for call in calls:
        if (stack[0] == call["name"]):
            if (_stackExistsInCalls(call["calls"] if "calls" in call else None, stack[1:])):
                return True
    return False

def _findStackDifferences(differences, recordingA, recordingB, calls, callStack):
    if (not _stackExistsInCalls(recordingB, callStack)):
        differences.append(callStack)
        return
    if (not calls):
        return
    for call in calls:
        nextCallStack = callStack[:]
        nextCallStack.append(call["name"])
        _findStackDifferences(differences, recordingA, recordingB, call["calls"] if "calls" in call else None, nextCallStack)

def _printStackDifferenceSummary(differences):
    lastCalls = []
    for stack in differences:
        lastCalls.append(stack[-1])
    uniqueLastCalls = set(lastCalls)

    print "Stacks diverged in " + str(len(differences)) + " places."
    for lastCall in uniqueLastCalls:
        print "    " + lastCall + " (" + str(lastCalls.count(lastCall)) + " instances)"

def main():
    parser = argparse.ArgumentParser(description='Compare recordings')
    parser.add_argument('recordingA', help='Recording for run A')
    parser.add_argument('recordingB', help='Recording for run B')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    recordingA = _loadRecording(args.recordingA)
    recordingB = _loadRecording(args.recordingB)

    differencesAB = []
    _findStackDifferences(differencesAB, recordingA, recordingB, recordingA, [])
    print "Differences between A and B:"
    _printStackDifferenceSummary(differencesAB)

    differencesBA = []
    _findStackDifferences(differencesBA, recordingB, recordingA, recordingB, [])
    print "Differences between B and A:"
    _printStackDifferenceSummary(differencesBA)

    #print "differences:"
    #differences.sort(key = len)
    #print json.dumps(differences, sort_keys = False, indent = 2)

    # TODO: finish this analysis.

if __name__ == "__main__":
    main()