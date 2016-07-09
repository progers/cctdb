#!/usr/bin/env python

# lldb command hooks for recording a calling context tree (CCT)
#
# To use, start lldb and run:
#     command script import recordCommand.py
#
# Use "help record" for additional instructions for using the record command.

import commands
import lldb
import optparse
from record.cct import CCT, Function
from record.record import record
import shlex

def createParser():
    usage = "usage: %prog [options]"
    description='''Record a calling context tree (tree of all function calls) starting at the
current function. Typical usage is to stop on a breakpoint then run "record -o cct.json" to record
all calls and write the output to cct.json.'''
    parser = optparse.OptionParser(description=description, prog="record", usage=usage)
    parser.add_option("-o", "--output", action="store", dest="output", help="write recording to an output file")
    parser.add_option("-a", "--allmodules", action="store_true", dest="allModules", help="do not restrict recording to the current module", default=False)
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
        cct = record(target, stayInCurrentModule = not options.allModules)
    except Exception as exception:
        result.SetError(str(exception))
    if isinstance(cct, CCT):
        if options.output:
            with open(options.output, 'w') as outputFile:
                outputFile.write(cct.asJson(0))
                print "Wrote recording to '" + options.output + "'"
        else:
            print cct.asJson(2)

def __lldb_init_module(debugger, dict):
    # This initializer is being run from LLDB in the embedded command interpreter
    parser = createParser()
    recordCallingContextTree.__doc__ = parser.format_help()
    debugger.HandleCommand("command script add -f recordCommand.recordCallingContextTree record")
    print "The \"record\" command has been installed, type \"help record\" for more information."
