# lldb script for generating calling context trees (CCT).
#
# This script drives lldb via python APIs to step through a program and generate a CCT.

from cct import CCT, Function
import commands
import optparse
import os
import platform
import sys

# Import LLDB
# The following code is from the process_events.py lldb example:
#     https://llvm.org/svn/llvm-project/lldb/trunk/examples/python/process_events.py
try: 
    # Just try for LLDB in case PYTHONPATH is already correctly setup
    import lldb
except ImportError:
    lldb_python_dirs = list()
    # lldb is not in the PYTHONPATH, try some defaults for the current platform
    platform_system = platform.system()
    if platform_system == "Darwin":
        # On Darwin, try the currently selected Xcode directory
        xcode_dir = commands.getoutput("xcode-select --print-path")
        if xcode_dir:
            lldb_python_dirs.append(os.path.realpath(xcode_dir + "/../SharedFrameworks/LLDB.framework/Resources/Python"))
            lldb_python_dirs.append(xcode_dir + "/Library/PrivateFrameworks/LLDB.framework/Resources/Python")
        lldb_python_dirs.append("/System/Library/PrivateFrameworks/LLDB.framework/Resources/Python")
    success = False
    for lldb_python_dir in lldb_python_dirs:
        if os.path.exists(lldb_python_dir):
            if not (sys.path.__contains__(lldb_python_dir)):
                sys.path.append(lldb_python_dir)
                try: 
                    import lldb
                except ImportError:
                    pass
                else:
                    success = True
                    break
    if not success:
        raise Exception("Couldn't locate the 'lldb' module, please set PYTHONPATH correctly")

def _getTarget(executable, verbose = False):
    debugger = lldb.SBDebugger.Create()
    target = debugger.CreateTarget(executable)
    if not target:
        raise Exception("Error creating target '" + executable + "'")
    return target

# Return all functions in a specified module.
def _listFunctions(module, verbose = False):
    functions = []
    # TODO(phil): Is this really the best way to list all functions?
    for symbol in module.symbols:
        if symbol.type == lldb.eSymbolTypeCode:
            functions.append(symbol.name)
    return functions

# List available functions, optionally filter by module.
def listFunctions(executable, module = None, verbose = False):
    target = _getTarget(executable, verbose)
    modules = [module] if module else listModules(executable, verbose)

    functions = []
    for module in modules:
        module = target.FindModule(lldb.SBFileSpec(module))
        if not module:
           raise Exception("Could not find module '" + module + "' in '" + executable + "'")
        functions.extend(_listFunctions(module, verbose))
    return functions

# List available modules.
def listModules(executable, verbose = False):
    target = _getTarget(executable, verbose)
    modules = []
    for module in target.modules:
        modules.append(str(module.file))
    return modules

# Given a thread with a current frame depth of N, record all N+1 calls and add these calls to
# a CCT subtree.
# TODO(phil): support inlined functions.
def _recordSubtreeCallsFromThread(cct, thread, module, verbose):
    if not thread:
        return

    frameDepth = thread.GetNumFrames()
    while True:
        stopReason = thread.GetStopReason()
        if not (stopReason == lldb.eStopReasonPlanComplete or stopReason == lldb.eStopReasonBreakpoint):
            return
        frame = thread.GetFrameAtIndex(0)
        if not frame:
            return
        if module and not str(frame.module.file) == module:
            thread.StepOutOfFrame(frame)
            continue

        thread.StepInto()
        frame = thread.GetFrameAtIndex(0)
        nextFrameDepth = thread.GetNumFrames()
        if nextFrameDepth > frameDepth:
            function = frame.GetFunction()
            if not function:
                continue
            nextFunctionCall = Function(function.GetName())
            cct.addCall(nextFunctionCall)
            _recordSubtreeCallsFromThread(nextFunctionCall, thread, module, verbose)
        elif nextFrameDepth < frameDepth:
            return

# Record a calling context tree from the current process.
# For each non-nested breakpoint, a top-level call is created in the CCT.
def _record(process, module, verbose):
    cct = CCT()
    while True:
        state = process.GetState()
        if state == lldb.eStateStopped:
            # TODO(phil): Support multiple threads by iterating over each here.
            thread = process.GetThreadAtIndex(0)
            if not thread:
                raise Exception("Thread terminated unexpectedly")
            if thread.GetStopReason() == lldb.eStopReasonSignal:
                process.Continue()
                continue
            if thread.GetStopReason() == lldb.eStopReasonBreakpoint or thread.GetStopReason() == lldb.eStopReasonPlanComplete:
                frame = thread.GetFrameAtIndex(0)
                if not frame:
                    break
                function = frame.GetFunction()
                if function:
                    if module and not str(frame.module.file) == module:
                        raise Exception("Stopped on a breakpoint but specified module (" + module + ") did not match breakpoint module (" + str(frame.module.file) + ")")
                    currentFunction = Function(function.GetName())
                    cct.addCall(currentFunction)
                    _recordSubtreeCallsFromThread(currentFunction, thread, module, verbose)
                    process.Continue()
        elif state == lldb.eStateExited:
            break
        else:
            stateString = process.GetTarget().GetDebugger().StateAsCString(state)
            process.Kill()
            raise Exception("Unexpected process state '" + stateString + "'")
            break
    return cct

# Record the calling context tree of a specific process.
def recordProcess(executable, pid, module = None, function = None, verbose = False):
    target = _getTarget(executable, verbose)
    target.GetDebugger().SetAsync(False)

    if not function:
        function = "main"
    target.BreakpointCreateByName(function, target.GetExecutable().GetFilename());

    attachInfo = lldb.SBAttachInfo(int(pid))
    error = lldb.SBError()
    process = target.Attach(attachInfo, error)

    if error.Fail():
        raise Exception("Error attaching to process: " + error.description)
    if not process:
        raise Exception("Unable to attach to process")

    return _record(process, module, verbose)

# Record the calling context tree of a command.
def recordCommand(executable, args = [], module = None, function = None, verbose = False):
    target = _getTarget(executable, verbose)
    target.GetDebugger().SetAsync(False)

    # TODO(phil): Launch in a stopped state instead of defaulting to "main".
    if not function:
        function = "main"
    target.BreakpointCreateByName(function, target.GetExecutable().GetFilename());

    process = target.LaunchSimple(args, None, os.getcwd())
    if not process:
        raise Exception("Could not launch '" + executable + "' with args '" + ",".join(args) + "'")

    return _record(process, module, verbose)
