# Class for recording calling context trees (CCT) using lldb.

# LLDB is not on the python path by default. Try to give a helpful error message if it isn't found.
try:
    import lldb
except ImportError:
    print "LLDB not found in PYTHONPATH. Run the following command to add it:"
    print "  export PYTHONPATH=/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python"
    raise Exception("Couldn't locate the 'lldb' module, please set PYTHONPATH correctly")
from cct import CCT, Function
import os
import platform
import sys
import warnings

class lldbRecorder:
    def __init__(self, executable):
        self._executable = executable
        self._target = lldb.SBDebugger.Create().CreateTarget(self._executable)
        if not self._target:
            raise Exception("Could not create target '" + self._executable + "'")
        self._target.GetDebugger().SetAsync(True)
        self._cct = None
        self._skipOptimizationWarning = False

    def cct(self):
        return self._cct

    def launchProcessThenRecord(self, args = [], moduleName = None, functionName = None):
        self._cct = None
        if not functionName:
            functionName = "main"
        self._createBreakpoint(functionName, moduleName)
        process = self._target.LaunchSimple(args, None, os.getcwd())
        if not process:
            raise Exception("Could not launch '" + self._executable + "' with args '" + ",".join(args) + "'")
        return self._recordFromBreakpoints(moduleName)

    def attachToProcessThenRecord(self, pid, moduleName = None, functionName = None):
        self._cct = None
        # TODO(phil): Launch in a stopped state instead of defaulting to "main".
        if not functionName:
            functionName = "main"
        self._createBreakpoint(functionName, moduleName)

        attachInfo = lldb.SBAttachInfo(int(pid))
        error = lldb.SBError()
        process = self._target.Attach(attachInfo, error)
        if error.Fail():
            raise Exception("Error attaching to process: " + error.description)
        if not process:
            raise Exception("Unable to attach to process")
        return self._recordFromBreakpoints(moduleName)

    def getModuleNames(self):
        # TODO(phil): This will not find modules in subprocesses. Not sure that can be fixed.
        moduleNames = []
        for module in self._target.modules:
            moduleNames.append(module.file.fullpath)
        return moduleNames

    def getFunctionNamesWithModuleName(self, moduleName):
        # TODO(phil): Is this really the best way to list all functions?
        functionNames = []
        module = self._target.FindModule(lldb.SBFileSpec(moduleName))
        if not module:
            raise Exception("Could not find module '" + moduleName + "'")
        for symbol in module.symbols:
            if symbol.type == lldb.eSymbolTypeCode:
                functionNames.append(symbol.name)
        return functionNames

    def getAllFunctionNames(self):
        functionNames = []
        for moduleName in self.getModuleNames():
            functionNames.extend(self.getFunctionNamesWithModuleName(moduleName))
        return functionNames

    # LLDB has stepping bugs if optimizations are enabled so give the user a heads up.
    # See: https://llvm.org/bugs/show_bug.cgi?id=27800
    def _checkForOptimizations(self, function):
        if self._skipOptimizationWarning:
            return
        if function and function.GetIsOptimized():
            message = ("Function '" + str(function.GetName()) + "' was compiled with optimizations "
                       "which can cause stepping issues. Consider re-compiling with -O0.")
            warnings.warn(message, RuntimeWarning)
            self._skipOptimizationWarning = True

    def _createBreakpoint(self, functionName, moduleName = None):
        self._target.BreakpointCreateByName(functionName, moduleName)
        if self._target.num_breakpoints <= 0:
            raise Exception("Failed to create function breakpoint.")

    def _ensureBreakpointExists(self, moduleName = None):
        if not self._target.GetProcess():
            raise Exception("No running process found")

        # Ensure a breakpoint was created (see: _createBreakpoint)
        # FIXME(phil): Turn this into a member variable instead of relying on lldb state.
        if self._target.num_breakpoints <= 0:
            raise Exception("Failed to create function breakpoint.")

        if moduleName and not self._target.FindModule(lldb.SBFileSpec(moduleName)):
            raise Exception("Unable to find specified module in target.")

        # Ensure that a breakpoint is active in our module.
        for breakpoint in self._target.breakpoint_iter():
            if breakpoint.GetNumLocations() <= 0:
                raise Exception("Could not break on function. Check the specified function name.")

    # Record a calling context tree from the current process.
    # For each non-nested breakpoint, a top-level call is created in the CCT.
    # TODO(phil): support stepping into new threads. Because LLDB doesn't support thread creation
    # callbacks, we'll step over the creation of new threads without stepping into them. There's some
    # discussion on this issue at http://lists.cs.uiuc.edu/pipermail/lldb-dev/2015-July/007728.html.
    def _recordFromBreakpoints(self, moduleName = None):
        self._ensureBreakpointExists(moduleName)
        if self._cct:
            raise Exception("Can only record one tree at a time.")
        self._cct = CCT()

        process = self._target.GetProcess()
        listener = self._target.GetDebugger().GetListener()

        # The current call leaf being processed.
        subtree = self._cct
        # The frame counts for each node in the subtree.
        subtreeFrameDepth = [ -1 ]

        # Continue if initially stopped.
        # FIXME(phil): Should we do this inside the main loop on the first stop?
        if process.GetState() == lldb.eStateStopped:
            process.Continue()

        # This is the main event loop where we wait for lldb to hit a breakpoint, and then step
        # through and record every function call below the breakpoint.
        # FIXME(phil): Factor out the tree management (adding fn calls, etc) from the event loop.
        while True:
            event = lldb.SBEvent()
            if not listener.WaitForEvent(1, event):
                # If no event occurs after 1s, control is returned to this thread. We handle any
                # events (signals, etc) and immediately return back to wait for events.
                continue
            if lldb.SBProcess.EventIsProcessEvent(event):
                state = lldb.SBProcess.GetStateFromEvent(event)
                if state == lldb.eStateStopped:
                    thread = process.GetSelectedThread()
                    stopReason = thread.GetStopReason()
                    if stopReason == lldb.eStopReasonBreakpoint:
                        frame = thread.GetFrameAtIndex(0)
                        if frame.is_inlined:
                            raise Exception("Breakpoints are not supported on inlined functions")
                        if subtree != self._cct:
                            raise Exception("Nested breakpoints should have been handled by stepping")

                        frameFunction = frame.GetFunction()
                        self._checkForOptimizations(frameFunction)
                        newFunctionCall = Function(frameFunction.GetName())
                        subtree.addCall(newFunctionCall)
                        subtreeFrameDepth.append(thread.GetNumFrames())
                        subtree = newFunctionCall

                        thread.StepInto()
                    elif stopReason == lldb.eStopReasonPlanComplete:
                        # Update current tree position given the current frame depth.
                        frameDepth = thread.GetNumFrames()
                        steppedOutOfBreakpoint = False
                        while frameDepth < subtreeFrameDepth[-1]:
                            subtree = subtree.parent
                            subtreeFrameDepth.pop()
                            if subtree == self._cct:
                                steppedOutOfBreakpoint = True
                                break
                        if steppedOutOfBreakpoint:
                            process.Continue()
                            continue

                        # If the frame depth is unchanged, do not record a new function call as
                        # we are still in the previous one. This will occur for all but the first
                        # line of a function.
                        if frameDepth == subtreeFrameDepth[-1]:
                            # FIXME(phil): Harden this check by verifying the function name.
                            thread.StepInto()
                            continue

                        # Stay within our specified module.
                        frame = thread.GetFrameAtIndex(0)
                        if moduleName and not str(frame.module.file.fullpath) == moduleName:
                            thread.StepOutOfFrame(frame)
                            continue

                        # Ignore inlined functions because the frame depth becomes unreliable.
                        if frame.is_inlined:
                            thread.StepInto()
                            continue

                        # We are only interested in function calls.
                        frameFunction = frame.GetFunction()
                        if not frameFunction:
                            thread.StepInto()
                            continue

                        self._checkForOptimizations(frameFunction)
                        newFunctionCall = Function(frameFunction.GetName())
                        subtree.addCall(newFunctionCall)
                        subtreeFrameDepth.append(frameDepth)
                        subtree = newFunctionCall

                        thread.StepInto()
                    elif stopReason == lldb.eStopReasonNone:
                        continue
                    elif stopReason == lldb.eStopReasonInvalid:
                        continue
                    elif stopReason == lldb.eStopReasonSignal:
                        # FIXME(phil): Check the actual signal and only continue for SIGSTOP.
                        process.Continue()
                    else:
                        raise Exception("Unhandled stepping stop reason: " + str(stopReason))
                elif state == lldb.eStateStepping:
                    raise Exception("Unhandled stepping process state.")
                elif state == lldb.eStateExited:
                    break
                elif state == lldb.eStateInvalid:
                    raise Exception("Invalid process state")
                elif state == lldb.eStateRunning:
                    continue
                else:
                    raise Exception("Unhandled process state: " + str(state))
            else:
                raise Exception("Unhandled event: " + str(event))
        return self._cct

    def __del__(self):
        if self._target and self._target.GetDebugger():
            # Must manually clean up, see: https://llvm.org/bugs/show_bug.cgi?id=27639.
            self._target.GetDebugger().DeleteTarget(self._target)
            self._target.GetDebugger().Terminate()
