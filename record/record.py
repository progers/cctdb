# Utility for recording calling context trees (CCT) using lldb.

from cct import CCT, Function
import lldb
import warnings

# Record a calling context tree rooted at the current frame.
# TODO(phil): support stepping into new threads. Because LLDB doesn't support thread creation
# callbacks, we'll step over the creation of new threads without stepping into them. There's some
# discussion on this issue at http://lists.cs.uiuc.edu/pipermail/lldb-dev/2015-July/007728.html.
def record(target, shouldStayWithinModule = True):
    thread = target.GetProcess().GetSelectedThread()
    frame = thread.GetSelectedFrame()
    function = frame.GetFunction()
    if not function:
        raise Exception("Debugger not stopped on a function.")

    cct = CCT()
    stayWithinModule = frame.GetModule() if shouldStayWithinModule else None
    recordFunctionAndSubtree(cct, thread, function, thread.GetNumFrames(), stayWithinModule)
    return cct

# Given a thread with a current frame depth of N, record all N+1 calls and add these calls to
# a CCT subtree.
def recordFunctionAndSubtree(tree, thread, function, frameCount, stayWithinModule):
    _warnAboutOptimizations(function)
    subtree = Function(function.GetName())
    tree.addCall(subtree)

    while _stoppedOnPlanOrBreakpoint(thread):
        thread.StepInto()
        nextFrame = thread.GetSelectedFrame()

        # Stay within our specified module.
        if stayWithinModule and not nextFrame.module == stayWithinModule:
            thread.StepOutOfFrame(nextFrame)
            continue

        # Ignore inlined functions because the frame depth becomes unreliable.
        if nextFrame.is_inlined:
            continue

        nextFrameCount = thread.GetNumFrames()
        if nextFrameCount > frameCount:
            nextFunction = nextFrame.GetFunction()
            if nextFunction:
                recordFunctionAndSubtree(subtree, thread, nextFunction, nextFrameCount, stayWithinModule)
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
