# Utility for recording calling context trees (CCT) using lldb.

from cct import CCT, Function
import lldb
import warnings

# Global variable to prevent showing the optimization warning multiple times.
skipOptimizationWarning = False

# Record a calling context tree rooted at the current frame.
# TODO(phil): support stepping into new threads. Because LLDB doesn't support thread creation
# callbacks, we'll step over the creation of new threads without stepping into them. There's some
# discussion on this issue at http://lists.cs.uiuc.edu/pipermail/lldb-dev/2015-July/007728.html.
def record(target, shouldStayWithinModule = True):
    cct = CCT()
    thread = target.GetProcess().GetSelectedThread()
    frame = thread.GetSelectedFrame()
    function = frame.GetFunction()
    if function:
        stayWithinModule = frame.GetModule() if shouldStayWithinModule else None
        # TODO(phil): refactor function creation into recordSubtreeCalls instead of duplicating it.
        functionCall = Function(function.GetName())
        cct.addCall(functionCall)
        recordSubtreeCalls(functionCall, thread, stayWithinModule)
    else:
        raise Exception("Debugger not stopped on a function.")
    return cct

# Given a thread with a current frame depth of N, record all N+1 calls and add these calls to
# a CCT subtree.
# TODO(phil): support stepping into new threads. Because LLDB doesn't support thread creation
# callbacks, we'll step over the creation of new threads without stepping into them. There's some
# discussion on this issue at http://lists.cs.uiuc.edu/pipermail/lldb-dev/2015-July/007728.html.
def recordSubtreeCalls(cct, thread, stayWithinModule, initialFrameDepth = None):
    if not thread:
        return

    if not initialFrameDepth:
        initialFrameDepth = thread.GetNumFrames()

    while True:
        stopReason = thread.GetStopReason()
        if not (stopReason == lldb.eStopReasonPlanComplete or stopReason == lldb.eStopReasonBreakpoint):
            return

        thread.StepInto()
        frame = thread.GetSelectedFrame()

        # Stay within our specified module.
        if stayWithinModule and not frame.module == stayWithinModule:
            thread.StepOutOfFrame(frame)
            continue

        # Ignore inlined functions because the frame depth becomes unreliable.
        if frame.is_inlined:
            continue

        frameDepth = thread.GetNumFrames()
        if frameDepth > initialFrameDepth:
            function = frame.GetFunction()
            if not function:
                continue
            # LLDB has stepping bugs if optimizations are enabled so give the user a heads up.
            # See: https://llvm.org/bugs/show_bug.cgi?id=27800
            global skipOptimizationWarning
            if not skipOptimizationWarning and function.GetIsOptimized():
                message = ("Function '" + str(function.GetName()) + "' was compiled with optimizations "
                           "which can cause stepping issues. Consider re-compiling with -O0.")
                warnings.warn(message, RuntimeWarning)
                skipOptimizationWarning = True
            functionCall = Function(function.GetName())
            cct.addCall(functionCall)
            recordSubtreeCalls(functionCall, thread, stayWithinModule, frameDepth)
        elif frameDepth < initialFrameDepth:
                return