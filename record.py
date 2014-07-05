#!/usr/bin/env python

# Calling Context Tree Recorder

import argparse
import os
from subprocess import Popen, PIPE
import re

DTRACE_PRIVILEGE_ERROR = 'DTrace requires additional privileges'
DTRACE_NOT_FOUND_ERROR = 'dtrace: command not found'
DTRACE_RECORD_SCRIPT = """
int shouldTrace;
dtrace:::BEGIN
{
  shouldTrace = 0;
}
pidPID:MODULE:FUNCTION:entry {
  shouldTrace = 1;
}
pidPID:MODULE:FUNCTION:return {
  shouldTrace = 0;
  exit(0);
}
pidPID:MODULE::entry
/shouldTrace == 1/
{
  printf("%s\\n", probefunc);
}
"""

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

# List available functions, optionally filter by module.
def _listFunctions(pid, module = None):
    if not module or module == 'list':
        module = ''
    args = '-ln "pid' + str(pid) + ':' + str(module) + '::entry"'
    parsed = _parseDtraceEntryList(_dtrace(args))
    functions = set(row[3] for row in parsed)
    return list(functions)

# List available modules.
def _listModules(pid):
    args = '-ln "pid' + str(pid) + ':::entry"'
    parsed = _parseDtraceEntryList(_dtrace(args))
    modules = set(row[2] for row in parsed)
    return list(modules)

# Record the calling context tree.
# If specified, limit the calling context tree to just code inside 'module' and 'function'
def _record(pid, module, function):
    if not module or module == 'list':
        module = ''
    if not function or function == 'list':
        function = ''
    recordScript = DTRACE_RECORD_SCRIPT
    recordScript = recordScript.replace('PID', str(pid))
    recordScript = recordScript.replace('MODULE', module)
    recordScript = recordScript.replace('FUNCTION', function)
    recordScript = recordScript.rstrip('\n')
    recordScript = recordScript.replace('\'', '\\\'')
    args = '-q -p ' + str(pid) + ' -n \'' + recordScript + '\''
    return _dtrace(args)

def main():
    parser = argparse.ArgumentParser(description='Record a calling context tree.')
    parser.add_argument('-p', '--pid', type=int, required=True, help='Process ID to record.')
    parser.add_argument('-f', '--function', help='Function to record, or blank to record all functions (use \'list\' to list functions).')
    parser.add_argument('-m', '--module', help='Module to record (use \'list\' to list modules).')
    args = parser.parse_args()

    if (not _pidRunning(args.pid)):
        print "Process %d is not running" % args.pid
        return

    if (args.module == 'list'):
        print '\n'.join(_listModules(args.pid))
        return;

    if (args.function == 'list'):
        print '\n'.join(_listFunctions(args.pid, args.module))
        return;

    print _record(args.pid, args.module, args.function)

if __name__ == "__main__":
    main()