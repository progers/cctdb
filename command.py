#!/usr/bin/env python

# lldb command hooks for recording a calling context tree (CCT)
#
# To use, start lldb and run:
#     command script import command.py
#
# Use "help record" for additional instructions for using the record command.

from cct import CCT
import commands
import lldb
import optparse
from record import record
import shlex

def createParser():
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(description="Record a calling context tree", prog="record", usage=usage)
    parser.add_option("-o", "--output", action="store", dest="output", help="write recording to an output file")
    # TODO: Add option to stay within a module.
    # TODO: Improve the built-in description to provide a simple example.
    return parser

def recordCallingContextTree(debugger, command, result, dict):
    parser = createParser()
    try:
        (options, args) = parser.parse_args(shlex.split(command))
    except:
        result.SetError("Failed to parse options")
        return

    target = debugger.GetSelectedTarget()
    if not target.IsValid():
        result.SetError("Target not valid")
        return
    process = target.GetProcess()
    if not process.IsValid():
        result.SetError("Process not valid")
        return
    thread = process.GetSelectedThread()
    if not thread.IsValid():
        result.SetError("Selected thread not valid")
        return
    frame = thread.GetSelectedFrame()
    if not frame.IsValid():
        result.SetError("Selected frame not valid")
        return

    cct = None
    try:
        cct = record(target)
    except Exception as exception:
        result.SetError(str(exception))
    if isinstance(cct, CCT):
        if options.output:
            with open(options.output, 'w') as outputFile:
                outputFile.write(cct.asJson(0))
        else:
            print cct.asJson(2)

def __lldb_init_module(debugger, dict):
    # This initializer is being run from LLDB in the embedded command interpreter
    parser = createParser()
    record.__doc__ = parser.format_help()
    debugger.HandleCommand("command script add -f command.recordCallingContextTree record")
    print "The \"record\" command has been installed, type \"help record\" for more information."
