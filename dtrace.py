# Dtrace script for generating calling context trees (CCT).
#
# Dtrace has various issues on OSX which make this approach to generating CCTs a little messy.

import json
import os
import re
from subprocess import Popen, PIPE
from tempfile import mkstemp

DTRACE_PRIVILEGE_ERROR = 'DTrace requires additional privileges'
DTRACE_NOT_FOUND_ERROR = 'dtrace: command not found'

RECORD_FORKED_PROCESS_WARNING = 'Process forked but cctdb does not follow child processes. Consider using the -p option to attach to a specific process.'

# dtrace script to print a stack trace at every function call in almost-json format
# (see _convertStacksToJson).
DTRACE_RECORD_SCRIPT = """
#pragma D option ustackframes=32

proc:::start
/ppid == $target/
{
  printf("{\\"type\\": \\"warning\\", \\"message\\": \\"RECORD_FORKED_PROCESS_WARNING\\"},\\n");
}
int shouldTraceFunction;
dtrace:::BEGIN
{
  shouldTraceFunction = 0;
  printf("[\\n{\\"type\\": \\"begin\\"},\\n");
}
dtrace:::END
{
  shouldTraceFunction = 0;
  printf("{\\"type\\": \\"end\\"}\\n]\\n");
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
  printf("{\\"type\\": \\"fn\\", \\"stack\\": DTRACE_BEGIN_STACK");
  ustack();
  printf("DTRACE_END_STACK},\\n");
}
"""

# Ustack helpers are broken on OSX so we can't write a json-formatted ustack. Instead, we emit begin
# and end stack markers (DTRACE_{BEGIN,END}_STACK) and post-process these to json in this function.
def _convertStacksToJson(recording):
    jsonString = ""
    currentIdx = 0
    startStackMarker = 'DTRACE_BEGIN_STACK'
    endStackMarker = 'DTRACE_END_STACK'
    startStackMarkerLength = len(startStackMarker)
    endStackMarkerLength = len(endStackMarker)
    while True:
        stackStartIdx = recording.find(startStackMarker, currentIdx)
        if (stackStartIdx == -1):
            jsonString += recording[currentIdx:]
            break

        # Copy up to the marker
        jsonString += recording[currentIdx:stackStartIdx]

        stackStartIdx += startStackMarkerLength
        stackEndIdx = recording.find(endStackMarker, stackStartIdx)
        if (stackEndIdx == -1):
            raise Exception('Error parsing dtrace stacktraces.')
        stackChunk = recording[stackStartIdx:stackEndIdx]
        stackChunk = stackChunk.strip()
        unparsedStack = stackChunk.split('\n') if len(stackChunk) > 0 else []
        parsedStack = []
        for call in unparsedStack:
            call = call.strip()
            # Strip the function call offset (e.g., functionName+0x123 -> functionName).
            offsetSeparatorIdx = call.find('+')
            if (offsetSeparatorIdx != -1):
                call = call[: offsetSeparatorIdx]
            # Strip non-ascii characters which can occur when dtrace overflows on long names.
            call = "".join([i for i in call if 31 < ord(i) < 127])
            parsedStack.append('"' + call + '"')
        jsonString += '[' + ','.join(parsedStack) + ']'
        currentIdx = stackEndIdx + endStackMarkerLength

    return jsonString

# Given a partial stack, do a best-effort calculation for the final depth of the partial stack.
# For example: Given the complete stack [main(), myFun(), printHappy()] and the partial stack
#              [myFun(), printHappy()], we can compute the depth of printHappy() as 3 deep.
def _calculateFrameDepth(completeStack, nextFramePartialStack):
    # Make a copy because it will be modified
    stack = completeStack[:]
    while (True):
        stackLength = len(stack)
        framesToCheck = min(stackLength, len(nextFramePartialStack) - 1)
        stacksMatch = True
        for frameIdx in range(0, framesToCheck):
            if (nextFramePartialStack[frameIdx + 1] != stack[stackLength - frameIdx - 1]):
                stacksMatch = False
                break
        if (stacksMatch):
            return stackLength
        elif (stackLength == 0):
            return 0
        # Pop up a frame and try again
        stack.pop()

# Convert a list of function calls with stacks into a tree.
# If there are multiple calls to the program's entry point (or, if function filtering was used),
# the returned tree will be a list of subtrees.
def _convertRecordingToCallTree(recording):
    recording = json.loads(_convertStacksToJson(recording))

    callsTree = []
    stack = []
    for fnCall in recording:
        if (fnCall["type"] != "fn"):
            continue
        if (not "stack" in fnCall):
            continue
        fnStack = fnCall["stack"]
        if (len(fnStack) == 0):
            continue
        depth = _calculateFrameDepth(stack, fnStack)
        if (depth == 0):
            # utrace() will occasionally jump from a stack of [a, b, c] to [a, b, c, d, e, f],
            # possibly due to issues rewinding RVO or inlined functions. Before assuming a
            # stack forms a new top-level call, check to see if the tree makes sense if
            # we assume up to N skipped frames. This should be lower than ustackframes in the
            # recording script.
            MAX_SKIPPED_STACK_FRAMES = 12
            for skippedFrames in range(1, min(MAX_SKIPPED_STACK_FRAMES, len(fnStack)-1)):
                depth = _calculateFrameDepth(stack, fnStack[skippedFrames:])
                if (depth > 0):
                    # Pretend the lower frames (e.g., 'e', 'f') never happened.
                    fnStack = fnStack[skippedFrames:]
                    break
        stack = stack[: depth]
        stack.append(fnStack[0])
        calls = callsTree
        for d in range(0, depth):
            if (not "calls" in calls[-1]):
                calls[-1]["calls"] = []
            calls = calls[-1]["calls"]
        newCall = {}
        newCall["name"] = fnStack[0]
        calls.append(newCall)
    return callsTree

# Run dtrace, returning the output as a string.
def _dtrace(args, verbose):
    # To prevent stderr/stdout from being interleaved in our dtrace data we use a temp file.
    tempFileDescriptor, tempFileName = mkstemp()
    args += ' -o \'' + tempFileName + '\''

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

    # Read the dtrace output from our tempfile, then free the file.
    tempFile = open(tempFileName, 'r')
    data = tempFile.read()
    tempFile.close()
    os.close(tempFileDescriptor)
    return data

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
    recordScript = DTRACE_RECORD_SCRIPT
    # : and , are special characters for dtrace, so swap them with the single-character wildcard.
    recordScript = recordScript.replace('MODULE', module.replace(':', '?').replace(',', '?'))
    recordScript = recordScript.replace('FUNCTION', function.replace(':', '?').replace(',', '?'))
    recordScript = recordScript.rstrip('\n')
    recordScript = recordScript.replace('\'', '\\\'')

    args = args + ' -q -n \'' + recordScript + '\''
    recording = _dtrace(args, verbose)

    if ('RECORD_FORKED_PROCESS_WARNING' in recording):
        print RECORD_FORKED_PROCESS_WARNING

    return _convertRecordingToCallTree(recording)
