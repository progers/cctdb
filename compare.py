#!/usr/bin/env python

# compare.py - compare the calling context trees of two runs.

import argparse
import collections
import dtrace

def _testOnlyReadFile(file):
    with open (file, "r") as myfile:
        data=myfile.read()
    return data

def _frequency(calls):
    callsList = calls.split('\n')
    counter = collections.Counter(callsList)
    return len(calls.split('\n'))

def main():
    parser = argparse.ArgumentParser(description='Compare the calls made by two commands')
    parser.add_argument('commandA', help='First command to run (use absolute paths, may include args')
    parser.add_argument('commandB', help='Second command to run (use absolute paths, may include args')
    parser.add_argument('-m', '--module', help='Filter by module')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    parser.add_argument('--testOnlyCallsA', help='xxxxxx')
    parser.add_argument('--testOnlyCallsB', help='xxxxxx')
    args = parser.parse_args()

    callsA = None
    if (args.testOnlyCallsA):
        callsA = _testOnlyReadFile(args.testOnlyCallsA)
    else:
        callsA = dtrace.record(args.commandA, args.module, args.function, args.verbose)
    #print 'calls made by a: ' + str(_frequency(callsA))

    callsB = None
    if (args.testOnlyCallsB):
        callsB = _testOnlyReadFile(args.testOnlyCallsB)
    else:
        callsB = dtrace.record(args.commandB, args.module, args.function, args.verbose)
    #print 'calls made by b: ' + str(_frequency(callsB))

    callsListA = callsA.split('\n')
    frequencyA = collections.Counter(callsListA)
    callsListB = callsB.split('\n')
    frequencyB = collections.Counter(callsListB)

    print "most common A:"
    mostCommonA = frequencyA.most_common(20)
    print '\n'.join(str(i) for i in mostCommonA)

    print "most common B:"
    mostCommonB = frequencyB.most_common(20)
    print '\n'.join(str(i) for i in mostCommonB)

if __name__ == "__main__":
    main()