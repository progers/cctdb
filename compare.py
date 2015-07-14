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

def main():
    parser = argparse.ArgumentParser(description='Compare recordings')
    parser.add_argument('recordingA', help='Recording for run A')
    parser.add_argument('recordingB', help='Recording for run B')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    recordingA = _loadRecording(args.recordingA)
    recordingB = _loadRecording(args.recordingB)

    lastTimestamp = 0
    for entry in recordingB:
        timestamp = entry["timestamp"]
        if (timestamp < lastTimestamp):
            print "Timestamps seem weird:"
            print entry
        lastTimestamp = timestamp

    # TODO: finish this analysis.

if __name__ == "__main__":
    main()