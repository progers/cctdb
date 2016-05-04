# Class for recording calling context trees (CCT) using lldb.

import lldb
from cct import CCT, Function
import os
import platform
import sys

class lldbRecorder:
    def __init__(self, executable):
        self._executable = executable
        self._target = lldb.SBDebugger.Create().CreateTarget(self._executable)
        if not self._target:
            raise Exception("Could not create target '" + self._executable + "'")
        # TODO(phil): Is this needed?
        self._target.GetDebugger().SetAsync(False)
        self._recording = False

    def launchProcessThenRecord(self, args = [], moduleName = None, functionName = None):
        if not functionName:
            functionName = "main"
        self._createBreakpoint(functionName, moduleName)
        process = self._target.LaunchSimple(args, None, os.getcwd())
        if not process:
            raise Exception("Could not launch '" + self._executable + "' with args '" + ",".join(args) + "'")
        return self._recordFromBreakpoint(moduleName)

    def attachToProcessThenRecord(self, pid, moduleName = None, functionName = None):
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
        return self._recordFromBreakpoint(moduleName)

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

    def _createBreakpoint(self, functionName, moduleName = None):
        self._target.BreakpointCreateByName(functionName, moduleName)
        if self._target.num_breakpoints <= 0:
            raise Exception("Failed to create function breakpoint.")

    # Given a thread with a current frame depth of N, record all N+1 calls and add these calls to
    # a CCT subtree.
    # TODO(phil): support stepping into new threads. Because LLDB doesn't support thread creation
    # callbacks, we'll step over the creation of new threads without stepping into them. There's some
    # discussion on this issue at http://lists.cs.uiuc.edu/pipermail/lldb-dev/2015-July/007728.html.
    def _recordSubtreeCallsFromThread(self, cct, thread, moduleName, initialFrameDepth = None):
        if not thread:
            return

        if not initialFrameDepth:
            initialFrameDepth = thread.GetNumFrames()

        while True:
            stopReason = thread.GetStopReason()
            if not (stopReason == lldb.eStopReasonPlanComplete or stopReason == lldb.eStopReasonBreakpoint):
                return

            thread.StepInto()
            frame = thread.GetFrameAtIndex(0)

            # Stay within our specified module.
            if moduleName and not str(frame.module.file.fullpath) == moduleName:
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
                functionCall = Function(function.GetName())
                cct.addCall(functionCall)
                self._recordSubtreeCallsFromThread(functionCall, thread, moduleName, frameDepth)
            elif frameDepth < initialFrameDepth:
                return

    # Suspend all running threads except nonStopThread. Returns the threads that were suspended.
    def _suspendOtherThreads(self, nonStopThread, process):
        nonStopThreadId = nonStopThread.GetThreadID()
        suspendedThreads = []
        for thread in process.threads:
            if thread.is_suspended:
                continue
            threadId = thread.GetThreadID()
            if threadId == nonStopThreadId:
                continue
            thread.Suspend()
            suspendedThreads.append(thread)
        return suspendedThreads

    def _resumeThreads(self, threads):
        for thread in threads:
            thread.Resume()

    # Record a calling context tree from the current process.
    # For each non-nested breakpoint, a top-level call is created in the CCT.
    def _recordFromBreakpoint(self, moduleName = None):
        if self._recording:
            raise Exception("Cannot record process that is already being recorded.")
        self._recording = True
        process = self._target.GetProcess()
        if not process:
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

        cct = CCT()
        while True:
            state = process.GetState()
            if state == lldb.eStateStopped:
                for thread in process.threads:
                    stopReason = thread.GetStopReason()
                    if stopReason == lldb.eStopReasonBreakpoint:
                        frame = thread.GetFrameAtIndex(0)
                        if frame.is_inlined:
                            raise Exception("Breakpoints are not supported on inlined functions.")
                        frameFunction = frame.GetFunction() if frame else None
                        if frameFunction:
                            if moduleName and not str(frame.module.file.fullpath) == moduleName:
                                raise Exception("Stopped on a breakpoint but specified module (" + moduleName + ") did not match breakpoint module (" + str(frame.module.file.fullpath) + ")")

                            suspendedThreads = self._suspendOtherThreads(thread, process)

                            currentFunction = Function(frameFunction.GetName())
                            cct.addCall(currentFunction)
                            self._recordSubtreeCallsFromThread(currentFunction, thread, moduleName)

                            self._resumeThreads(suspendedThreads)

                process.Continue()
            elif state == lldb.eStateExited:
                break
            else:
                stateString = self._target.GetDebugger().StateAsCString(state)
                process.Kill()
                raise Exception("Unexpected process state '" + stateString + "'")
                break
        return cct

    def __del__(self):
        if self._target and self._target.GetDebugger():
            self._target.GetDebugger().DeleteTarget(self._target)
            # FIXME(phil): This line will prevent an lldb internal segfault but will cause tests to
            # fail to attach. Filed: https://llvm.org/bugs/show_bug.cgi?id=27639
            #self._target.GetDebugger().Terminate()
