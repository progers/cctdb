#!/usr/bin/env python

# record.py - List a calling context tree.
#
# FIXME(phil): Switch to a kernel-level function tracing (dtrace, utrace/systemtap, etc.) over LLDB.
# Kernel hooks are difficult to use for reliably recording all function calls in complex codebases
# due to inlining, RVO, etc (see [1]). Relying on LLDB's complex source mapping logic is slow but
# fairly reliable, and is cross-platform.
# [1] https://github.com/progers/cctdb/blob/b08176b9f24c95a96ff6a22a6e63d176cc0916ae/dtrace.py

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

    recorder = lldbRecorder(args.executable)
    try:
        if (args.pid):
            recorder.attachToProcessThenRecord(args.pid, args.module, args.function)
        else:
            recorder.launchProcessThenRecord(leftoverArgs, args.module, args.function)
    except KeyboardInterrupt:
        pass

    result = recorder.cct()
    if result:
        # Serialize the result if it is a CCT.
        if isinstance(result, CCT):
            result = result.asJson(2)
        print result

if __name__ == "__main__":
    main()
