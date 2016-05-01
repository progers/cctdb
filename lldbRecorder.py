# Class for recording calling context trees (CCT) using lldb.

import lldb
from cct import CCT, Function
import commands
import optparse
import os
import platform
import sys

class lldbRecorder:
    def __init__(self, executable):
        self._executable = executable
        self._target = lldb.SBDebugger.Create().CreateTarget(self._executable)
        if not self._target:
            raise Exception("Could not create target '" + self._executable + "'")

    def launchProcess(self, args = []):
        process = self._target.LaunchSimple(args, None, os.getcwd())
        if not process:
            raise Exception("Could not launch '" + self._executable + "' with args '" + ",".join(args) + "'")

    def getModules(self):
        # TODO(phil): This will not find modules in subprocesses. Not sure that can be fixed.
        modules = []
        for module in self._target.modules:
            modules.append(module.file.basename)
        return modules

    def getFunctionsInModule(self, moduleString):
        # TODO(phil): Is this really the best way to list all functions?
        functions = []
        module = self._target.FindModule(lldb.SBFileSpec(moduleString))
        if not module:
            raise Exception("Could not find module '" + moduleString + "'")
        for symbol in module.symbols:
            if symbol.type == lldb.eSymbolTypeCode:
                functions.append(symbol.name)
        return functions

    def getAllFunctions(self):
        functions = []
        for module in self.getModules():
            functions.extend(self.getFunctionsInModule(module))
        return functions

    def __del__(self):
        if self._target and self._target.GetDebugger():
            self._target.GetDebugger().Terminate()
