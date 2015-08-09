#!/usr/bin/env python

# record.py - List a calling context tree.
# TODO(pdr): Add an integration test for recording.

import argparse
from cct import CCT
import json
import lldbHelper

def main():
    parser = argparse.ArgumentParser(description='Record a calling context tree.')
    parser.add_argument('-e', '--executable', help='Executable to run (additional arguments are forwarded to this executable)')
    parser.add_argument('-p', '--pid', help='Process id')
    parser.add_argument('-m', '--module', help='Filter by module')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args, leftoverArgs = parser.parse_known_args()

    result = None

    if (args.executable):
        result = lldbHelper.recordCommand(args.executable, leftoverArgs, args.module, args.function, args.verbose)
    elif (args.pid):
        result = lldbHelper.recordProcess(args.pid, args.module, args.function, args.verbose)
    else:
        print "Must specify either --executable or --pid"
        return

    if result:
        # Serialize the result if it is a CCT.
        if isinstance(result, CCT):
            result = result.asJson(2)
        print result

if __name__ == "__main__":
    main()