# lldb script for generating calling context trees (CCT).
#
# TODO: DOC ME

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

def _runCommand(interpreter, command):
    returnObject = lldb.SBCommandReturnObject()
    interpreter.HandleCommand(command, returnObject)
    if returnObject.Succeeded():
        return returnObject.GetOutput()
    else:
        print returnObject

def _getTarget(executable, verbose = False):
    debugger = lldb.SBDebugger.Create()
    # TODO(phil): Async or sync?
    # debugger.SetAsync(False)
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

# Record the calling context tree of a specific process.
def recordProcess(pid, module = None, function = None, verbose = False):
    raise Exception("recordProcess not implemented")

# Record the calling context tree of a command.
def recordCommand(command, module = None, function = None, verbose = False):
    raise Exception("recordCommand not implemented")
