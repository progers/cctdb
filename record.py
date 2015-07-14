#!/usr/bin/env python

# record.py - List all function calls made by an command.

import argparse
import dtrace
import json

def main():
    parser = argparse.ArgumentParser(description='Record a calling context tree.')
    parser.add_argument('-c', '--command', help='Command to run (use absolute paths, may include args')
    parser.add_argument('-p', '--pid', help='Process id')
    parser.add_argument('-m', '--module', help='Filter by module')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('-o', '--out', help='Ouput file')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    result = None

    if (args.command):
        result = dtrace.recordCommand(args.command, args.module, args.function, args.verbose)
    elif (args.pid):
        result = dtrace.recordProcess(args.pid, args.module, args.function, args.verbose)
    else:
        print "Must specify either --command [command] or --process"
        return

    if result:
        if (args.out):
            outfile = open(args.out, 'w')
            json.dump(result, outfile, sort_keys = False, indent = 2)
            outfile.close()
        else:
            print result

if __name__ == "__main__":
    main()