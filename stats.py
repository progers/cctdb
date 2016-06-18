#!/usr/bin/env python

# stats.py - calling context tree stats.

import argparse
from collections import defaultdict
import json
from record.cct import CCT, Function

def _loadCCT(file):
    with open (file, 'r') as inFile:
        data = inFile.read()
    return CCT.fromJson(data)

def _countFunctionCallNames(subtree, functionNameCount):
    for function in subtree.calls:
        functionNameCount[function.name] += 1
        _countFunctionCallNames(function, functionNameCount)

def _topCalledFunctionCallNames(cct, count):
    functionNamesCount = defaultdict(int)
    _countFunctionCallNames(cct, functionNamesCount)
    sortedFunctionNameCount = [(functionNamesCount[name], name) for name in functionNamesCount]
    sortedFunctionNameCount.sort()
    sortedFunctionNameCount.reverse()
    return sortedFunctionNameCount[:count]

def main():
    parser = argparse.ArgumentParser(description="Calling context tree stats")
    parser.add_argument("recording", help="Calling context tree recording")
    args = parser.parse_args()

    cct = _loadCCT(args.recording)

    print "Top called functions:"
    for count, functionName in _topCalledFunctionCallNames(cct, 100):
        print "{:12}".format(count) + "  " + functionName

if __name__ == "__main__":
    main()
