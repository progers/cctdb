#!/usr/bin/env python

# compare.py - compare the calling context trees of two runs.

import argparse
import collections
import dtrace
import json
import os.path

def _loadCallsFile(file):
    if (not os.path.isfile(file)):
        raise Exception('File not found: ' + file)

    with open (file, "r") as myfile:
        data=myfile.read()
    return json.loads(data)

def _frequency(calls):
    callsList = calls.split('\n')
    counter = collections.Counter(callsList)
    return len(calls.split('\n'))

def main():
    parser = argparse.ArgumentParser(description='Compare calls')
    parser.add_argument('callsFileA', help='Calls file for run A')
    parser.add_argument('callsFileB', help='Calls file for run B')
    parser.add_argument('-m', '--module', help='Filter by module')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    callsA = _loadCallsFile(args.callsFileA)
    callsB = _loadCallsFile(args.callsFileB)

    frequencyA = collections.Counter(callsA)
    frequencyB = collections.Counter(callsB)

    print "most common A:"
    mostCommonA = frequencyA.most_common(20)
    print '\n'.join(str(i) for i in mostCommonA)

    print "most common B:"
    mostCommonB = frequencyB.most_common(20)
    print '\n'.join(str(i) for i in mostCommonB)

if __name__ == "__main__":
    main()