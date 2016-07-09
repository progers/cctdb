# Utility for recording calling context trees (CCT) using lldb.

from cct import CCT, Function
import lldb
import re
import warnings

# Record a calling context tree rooted at the current frame.
# TODO(phil): support stepping into new threads. Because LLDB doesn't support thread creation
# callbacks, we'll step over the creation of new threads without stepping into them. There's some
# discussion on this issue at http://lists.cs.uiuc.edu/pipermail/lldb-dev/2015-July/007728.html.
def record(target, stayInCurrentModule = True, functionNameRegex = None):
    thread = target.GetProcess().GetSelectedThread()
    frame = thread.GetSelectedFrame()
    function = frame.GetFunction()
    if not function:
        raise Exception("Debugger not stopped on a function.")

    cct = CCT()
    stayInModule = frame.GetModule() if stayInCurrentModule else None
    regex = re.compile(functionNameRegex) if functionNameRegex else None
    _recordFunctionAndSubtree(cct, thread, function, thread.GetNumFrames(), stayInModule, regex)
    return cct

# Given a thread with a current frame depth of N, record all N+1 calls and add these calls to
# a CCT subtree.
def _recordFunctionAndSubtree(tree, thread, function, frameCount, stayInModule, regex):
    # Skip this subtree if the regex does not match the function name.
    functionName = function.GetName()
    if regex and not regex.match(functionName):
        thread.StepOutOfFrame(thread.GetSelectedFrame())
        return

    _warnAboutOptimizations(function)
    subtree = Function(functionName)
    tree.addCall(subtree)

    while _stoppedOnPlanOrBreakpoint(thread):
        thread.StepInto()
        nextFrame = thread.GetSelectedFrame()

        # Stay within our specified module.
        if stayInModule and not nextFrame.module == stayInModule:
            thread.StepOutOfFrame(nextFrame)
            continue

        # Ignore inlined functions because the frame depth becomes unreliable.
        if nextFrame.is_inlined:
            continue

        nextFrameCount = thread.GetNumFrames()
        if nextFrameCount > frameCount:
            nextFunction = nextFrame.GetFunction()
            if nextFunction:
                _recordFunctionAndSubtree(subtree, thread, nextFunction, nextFrameCount, stayInModule, regex)
        elif nextFrameCount < frameCount:
            return

def _stoppedOnPlanOrBreakpoint(thread):
    stopReason = thread.GetStopReason()
    return stopReason == lldb.eStopReasonPlanComplete or stopReason == lldb.eStopReasonBreakpoint

# LLDB has stepping bugs if optimizations are enabled so give the user a heads up.
# See: https://llvm.org/bugs/show_bug.cgi?id=27800
#
# TODO: Investigate if we can dynamically change LLDB settings (e.g., use-fast-stepping,
# inline-breakpoint-strategy) to avoid these bugs.
alreadyShowedOptimizationWarning = False
def _warnAboutOptimizations(function):
    global alreadyShowedOptimizationWarning
    if not alreadyShowedOptimizationWarning and function.GetIsOptimized():
        message = ("Function '" + str(function.GetName()) + "' was compiled with optimizations "
                   "which can cause stepping issues. Consider re-compiling with -O0.")
        warnings.warn(message, RuntimeWarning)
        alreadyShowedOptimizationWarning = True
