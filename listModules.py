#!/usr/bin/env python

# listModules.py - List all module names in an executable.

import argparse
from lldbRecorder import lldbRecorder

def main():
    parser = argparse.ArgumentParser(description='List all module names of an executable.')
    parser.add_argument('executable', help='Path to executable')
    args = parser.parse_args()

    moduleNames = lldbRecorder(args.executable).getModuleNames()
    if (moduleNames):
        print '\n'.join(moduleNames)

if __name__ == "__main__":
    main()
