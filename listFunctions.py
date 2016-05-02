#!/usr/bin/env python

# listFunctions.py - List all function names in an executable.

import argparse
from lldbRecorder import lldbRecorder

def main():
    parser = argparse.ArgumentParser(description='List all function names of an executable.')
    parser.add_argument('executable', help='Path to executable')
    parser.add_argument('-m', '--module', help='Module to filter by')
    args = parser.parse_args()

    if args.module:
        functionNames = lldbRecorder(args.executable).getFunctionNamesWithModuleName(args.module)
        if (functionNames):
            print '\n'.join(functionNames)
    else:
        functionNames = lldbRecorder(args.executable).getAllFunctionNames()
        if (functionNames):
            print '\n'.join(functionNames)

if __name__ == "__main__":
    main()
