#!/usr/bin/env python

# record.py - List a calling context tree.

import argparse
from cct import CCT
import json
from lldbRecorder import lldbRecorder

def main():
    parser = argparse.ArgumentParser(description='Record a calling context tree.')
    parser.add_argument('executable', help='Executable to run (any additional arguments are forwarded to this executable)')
    parser.add_argument('-p', '--pid', help='Process id')
    parser.add_argument('-m', '--module', help='Filter by module')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    args, leftoverArgs = parser.parse_known_args()

    result = None
    if (args.pid):
        result = lldbRecorder(args.executable).attachToProcessThenRecord(args.pid, args.module, args.function)
    else:
        result = lldbRecorder(args.executable).launchProcessThenRecord(leftoverArgs, args.module, args.function)

    if result:
        # Serialize the result if it is a CCT.
        if isinstance(result, CCT):
            result = result.asJson(2)
        print result

if __name__ == "__main__":
    main()
