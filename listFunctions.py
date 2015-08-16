#!/usr/bin/env python

# listFunctions.py - List all functions in an executable.

import argparse
import lldbHelper

def main():
    parser = argparse.ArgumentParser(description='List all functions of an executable.')
    parser.add_argument('executable', help='Path to executable')
    parser.add_argument('-m', '--module', help='Module to filter by')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    functions = lldbHelper.listFunctions(args.executable, args.module, args.verbose)
    if (functions):
        print '\n'.join(functions)

if __name__ == "__main__":
    main()