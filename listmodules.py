#!/usr/bin/env python

# listmodules.py - List all modules in an executable.

import argparse
import dtrace

def main():
    parser = argparse.ArgumentParser(description='List all modules of an executable.')
    parser.add_argument('executable', help='Absolute path to executable')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    modules = dtrace.listModules(args.executable, args.verbose)
    if (modules):
        print '\n'.join(modules)

if __name__ == "__main__":
    main()