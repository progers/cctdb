#!/usr/bin/env python

# record.py - List all function calls made by an command.

import argparse
import dtrace

def main():
    parser = argparse.ArgumentParser(description='Record a calling context tree.')
    parser.add_argument('command', help='Command to run (use absolute paths, may include args')
    parser.add_argument('-m', '--module', help='Filter by module')
    parser.add_argument('-f', '--function', help='Filter for calls made in a specific function')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    calls = dtrace.record(args.command, args.module, args.function, args.verbose)
    if (calls):
        print calls

if __name__ == "__main__":
    main()