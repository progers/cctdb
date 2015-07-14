# dtrace helper functions

import json
import re
from subprocess import Popen, PIPE

DTRACE_PRIVILEGE_ERROR = 'DTrace requires additional privileges'
DTRACE_NOT_FOUND_ERROR = 'dtrace: command not found'

DTRACE_JSON_RECORD_SCRIPT = """
#pragma D option ustackframes=6

proc:::start
/ppid == $target/
{
  printf("{\\"type\\": \\"warning\\", \\"message\\": \\"Process forked but cctdb does not follow child processes. Consider using the -p option to attach to a specific process.\\"},\\n");
}
int shouldTraceFunction;
dtrace:::BEGIN
{
  shouldTraceFunction = 0;
  printf("[\\n{\\"type\\": \\"begin\\", \\"timestamp\\": %d},\\n", timestamp);
}
dtrace:::END
{
  shouldTraceFunction = 0;
  printf("{\\"type\\": \\"end\\", \\"timestamp\\": %d}\\n]\\n", timestamp);
}
pid$target:MODULE:FUNCTION:entry
{
  shouldTraceFunction++;
}
pid$target:MODULE:FUNCTION:return
{
  shouldTraceFunction--;
}
pid$target:MODULE::entry
/shouldTraceFunction >= 1/
{
  printf("{\\"type\\": \\"function\\", \\"name\\": \\"%s\\", \\"timestamp\\": %d, \\"stack\\": DTRACE_BEGIN_STACK", probefunc, timestamp);
  ustack(6);
  printf("DTRACE_END_STACK},\\n");
}
"""

# Ustack helpers are broken on OSX so we can't write a json-formatted ustack. Instead, we emit begin
# and end stack markers (DTRACE_{BEGIN,END}_STACK) and post-process these into valid json.
def _convertStacksToJson(data):
    jsonString = ""
    currentIdx = 0
    startStackMarker = 'DTRACE_BEGIN_STACK'
    endStackMarker = 'DTRACE_END_STACK'
    startStackMarkerLength = len(startStackMarker)
    endStackMarkerLength = len(endStackMarker)
    while True:
        stackStartIdx = data.find(startStackMarker, currentIdx)
        if (stackStartIdx == -1):
            jsonString += data[currentIdx:]
            break

        # Copy up to the marker
        jsonString += data[currentIdx:stackStartIdx]

        stackStartIdx += startStackMarkerLength
        stackEndIdx = data.find(endStackMarker, stackStartIdx)
        if (stackEndIdx == -1):
            raise Exception('Error parsing dtrace stacktraces.')
        stackChunk = data[stackStartIdx:stackEndIdx]
        stackChunk = stackChunk.lstrip('\n')
        stackChunk = stackChunk.rstrip('\n') + '"'
        stackChunk = stackChunk.replace('\n', '",')
        stackChunk = stackChunk.replace('              ', '"')
        # Strip non-ascii characters which can occur when dtrace hits very long symbols (over 1024).
        stackChunk = "".join([i for i in stackChunk if 31 < ord(i) < 127])
        stackChunk = '[' + stackChunk + ']'
        jsonString += stackChunk

        currentIdx = stackEndIdx + endStackMarkerLength

    return jsonString

# Run dtrace, returning the output as a string.
def _dtrace(args, verbose):
    if (verbose):
        print 'dtrace ' + args
    process = Popen('dtrace ' + args, stderr=PIPE, stdout=PIPE, shell=True)
    output, errors = process.communicate()
    if (errors):
        if (DTRACE_PRIVILEGE_ERROR in errors):
            raise Exception('Additional privileges needed. Try running with sudo.')
        if (DTRACE_NOT_FOUND_ERROR in errors):
            raise Exception('dtrace not found. Try installing dtrace.')
        if (not output):
            raise Exception(errors)
    return output

# Parse the dtrace list output of the format: ID PROVIDER MODULE FUNCTION_NAME entry.
def _parseEntryList(input):
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
def listFunctions(executable, module = None, verbose = False):
    if not module:
        module = ''
    args = '-ln \'pid$target:' + module + '::entry\' -c \'' + executable + '\''
    parsed = _parseEntryList(_dtrace(args, verbose))
    functions = set(row[3] for row in parsed)
    return list(functions)

# List available modules.
def listModules(executable, verbose = False):
    # Another option is to use "-lm 'pid$target:' ...". This will be much slower, though it will
    # return all modules instead of just those with entry functions.
    args = '-ln \'pid$target:::entry\' -c \'' + executable + '\''
    parsed = _parseEntryList(_dtrace(args, verbose))
    modules = set(row[2] for row in parsed)
    return list(modules)

# Record the calling context tree of a specific process.
def recordProcess(pid, module = None, function = None, verbose = False):
    return _record('-p ' + str(pid), module, function, verbose)

# Record the calling context tree of a command.
def recordCommand(command, module = None, function = None, verbose = False):
    return _record('-c \'' + command + '\'', module, function, verbose)

# Record the calling context tree.
# If specified, limit the calling context tree to just code inside 'module' and 'function'
def _record(args, module = None, function = None, verbose = False):
    if not module:
        module = ''
    if not function:
        function = ''
    recordScript = DTRACE_JSON_RECORD_SCRIPT
    # : and , are special characters for dtrace, so swap them with the single-character wildcard.
    recordScript = recordScript.replace('MODULE', module.replace(':', '?').replace(',', '?'))
    recordScript = recordScript.replace('FUNCTION', function.replace(':', '?').replace(',', '?'))
    recordScript = recordScript.rstrip('\n')
    recordScript = recordScript.replace('\'', '\\\'')

    args = args + ' -q -n \'' + recordScript + '\''
    data = json.loads(_convertStacksToJson(_dtrace(args, verbose)))

    # Remove any recording warnings and print them before passing the data along.
    for i in xrange(len(data) - 1, -1, -1):
        dataType = data[i]["type"]
        if (not dataType):
            continue
        if (dataType == "warning"):
            print data[i]["message"] + "\n"
            del data[i]
    return data