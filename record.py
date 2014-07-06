#!/usr/bin/env python

# Calling Context Tree Recorder

import argparse
import os
from subprocess import Popen, PIPE
import re
import json

DTRACE_PRIVILEGE_ERROR = 'DTrace requires additional privileges'
DTRACE_NOT_FOUND_ERROR = 'dtrace: command not found'
DTRACE_RECORD_SCRIPT = """
int shouldTraceFunction;
int stopAfterOneFunction;
dtrace:::BEGIN
{
  shouldTraceFunction = 0;
  stopAfterOneFunction = STOPAFTERONE;
}
pidPID:MODULE:FUNCTION:entry {
  shouldTraceFunction = 1;
}
pidPID:MODULE:FUNCTION:return
/stopAfterOneFunction == 1/
{
  shouldTraceFunction = 0;
  exit(0);
}
pidPID:MODULE:FUNCTION:return
/stopAfterOneFunction == 0/
{
  shouldTraceFunction = 0;
}
pidPID:MODULE::entry
/shouldTraceFunction == 1/
{
  printf("%s\\n", probefunc);
}
"""

# Program is a union for either a running program (with a pid) or
# a program we need to launch.
class Program:
    def __init__(self, pid, run):
        if (pid and isinstance(pid, int)):
            self.launchArgs = ''
            self.pid = str(pid)
        else:
            self.launchArgs = '-c \'' + run + '\''
            self.pid = '$target'

# Check if a PID is actually running.
def _pidRunning(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

# Run dtrace, returning the output as a string.
def _dtrace(args):
    process = Popen('dtrace ' + args, stderr=PIPE, stdout=PIPE, shell=True)
    output, errors = process.communicate()
    if (errors):
        if (DTRACE_PRIVILEGE_ERROR in errors):
            raise Exception('Additional privileges needed. Try running with sudo.')
        if (DTRACE_NOT_FOUND_ERROR in errors):
            raise Exception('Dtrace not found. Try installing dtrace.')
        if (not output):
            raise Exception(errors)
    return output

# Parse the dtrace list output of the format: ID PROVIDER MODULE FUNCTION_NAME entry.
def _parseDtraceEntryList(input):
    pattern = re.compile(r'\s*(?P<id>\d+)\s+(?P<provider>[^\s]+)\s+(?P<module>[^\s]+)\s+(?P<function>.*)\sentry')
    output = []
    lines = str.splitlines(input)
    for line in lines:
        matches = pattern.search(line)
        if matches:
            match = []
            match.append(matches.group('id'))
            match.append(matches.group('provider'))
            match.append(matches.group('module'))
            match.append(matches.group('function'))
            output.append(match)
    return output

# List available modules and functions.
def _listModulesAndFunctions(program):
    args = '-ln \'pid' + program.pid + ':::entry\' ' + program.launchArgs
    parsed = _parseDtraceEntryList(_dtrace(args))
    modulesAndFunctions = set(('module(' + row[2] + ') function(' + row[3] + ')') for row in parsed)
    return list(modulesAndFunctions)

# List available functions, optionally filter by module.
def _listFunctions(program, module = None):
    if not module or module == 'list':
        module = ''
    args = '-ln \'pid' + program.pid + ':' + module + '::entry\' ' + program.launchArgs
    parsed = _parseDtraceEntryList(_dtrace(args))
    functions = set(row[3] for row in parsed)
    return list(functions)

# List available modules.
def _listModules(program):
    args = '-ln \'pid' + program.pid + ':::entry\' ' + program.launchArgs
    parsed = _parseDtraceEntryList(_dtrace(args))
    modules = set(row[2] for row in parsed)
    return list(modules)

# Group functionCalls by function and output as a json array.
def _formatCallsAsJson(functionCalls, function):
    callsByProbe = [];
    currentCalls = [];
    calls = str.splitlines(functionCalls)
    for call in calls:
        if (not call or call == ''):
            continue
        if (call == function):
            if (len(currentCalls) > 1):
                callsByProbe.append(currentCalls)
            currentCalls = [call]
        else:
            currentCalls.append(call)
    if (len(currentCalls) > 1):
        callsByProbe.append(currentCalls)
    return json.dumps(callsByProbe)

# Record the calling context tree.
# If specified, limit the calling context tree to just code inside 'module' and 'function'
def _record(program, module, function):
    if not module or module == 'list':
        module = ''
    if not function or function == 'list':
        function = ''
    recordScript = DTRACE_RECORD_SCRIPT
    recordScript = recordScript.replace('PID', program.pid)
    recordScript = recordScript.replace('MODULE', module.replace(':', '?'))
    recordScript = recordScript.replace('FUNCTION', function.replace(':', '?'))
    if (program.launchArgs or module == ''):
        recordScript = recordScript.replace('STOPAFTERONE', '0')
    else:
        recordScript = recordScript.replace('STOPAFTERONE', '1')
    recordScript = recordScript.rstrip('\n')
    recordScript = recordScript.replace('\'', '\\\'')
    if (program.launchArgs):
        additionalArgs = program.launchArgs
    else:
        additionalArgs = '-p ' + program.pid
    args = additionalArgs + ' -q -n \'' + recordScript + '\''
    return _formatCallsAsJson(_dtrace(args), function)

def main():
    parser = argparse.ArgumentParser(description='Record a calling context tree.')
    parser.add_argument('-r', '--run', help='Program to launch (alternatively, use --pid).')
    parser.add_argument('-p', '--pid', type=int, help='Process ID to record (alternatively, use --run).')
    parser.add_argument('-f', '--function', help='Function to record, or blank to record all functions (use \'list\' to list functions).')
    parser.add_argument('-m', '--module', help='Module to record (use \'list\' to list modules).')
    args = parser.parse_args()

    if (not args.pid and not args.run):
        print "Either --run [program] or --pid [process id] is required."
        return

    if (args.pid and not _pidRunning(args.pid)):
        print "Process %d is not running" % args.pid
        return

    program = Program(args.pid, args.run)

    if (args.module == 'list' and args.function == 'list'):
        print '\n'.join(_listModulesAndFunctions(program))
        return

    if (args.module == 'list'):
        print '\n'.join(_listModules(program))
        return;

    if (args.function == 'list'):
        print '\n'.join(_listFunctions(program, args.module))
        return

    print _record(program, args.module, args.function)

if __name__ == "__main__":
    main()