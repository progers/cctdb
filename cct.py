# cct.py - calling context tree
#
# A Calling Context Tree (CCT) has a single root which contains multiple calls to Functions which
# can themselves have other calls.

from collections import defaultdict
import json
import re
import subprocess

class Function(object):

    def __init__(self, name):
        self.calls = []
        self.name = name
        self.parent = None
        self._callCountsByName = defaultdict(int)

    def isRoot(self):
        return False

    def addCall(self, call):
        if call.parent:
            raise ValueError("Function is already called by an existing Function.")
        if not call.name:
            raise ValueError("Function cannot be added without a name.")
        self.calls.append(call)
        self._callCountsByName[call.name] += 1
        call.parent = self

    def callCountToFunctionName(self, name):
        return self._callCountsByName[name]

    def callStack(self):
        stack = []
        if self.parent:
            stack.extend(self.parent.callStack())
        stack.append(self)
        return stack

    def callNameStack(self):
        nameStack = []
        for call in self.callStack():
            nameStack.append(call.name)
        return nameStack

    def uniqueCallNames(self):
        return self._callCountsByName.keys()

    def _collectAllUniqueCallNames(self, names):
        names.add(self.name)
        for call in self.calls:
            call._collectAllUniqueCallNames(names)

    def _demangle(self, demangleMap):
        if (self.name):
            oldName = self.name
            self.name = demangleMap[oldName]
        oldCallCountsByName = self._callCountsByName
        self._callCountsByName = defaultdict(int)
        for oldName, count in oldCallCountsByName.iteritems():
            self._callCountsByName[demangleMap[oldName]] = count
        for call in self.calls:
            call._demangle(demangleMap)

    def asJson(self, indent = None):
        return json.dumps(self, sort_keys=False, indent=indent, cls=FunctionJSONEncoder)

    @staticmethod
    def fromJson(string):
        return json.loads(string, cls=FunctionJSONDecoder)

# A CCT is the root for a calling context tree and represents the program entry point.
class CCT(Function):

    def __init__(self):
        Function.__init__(self, None)

    def asJson(self, indent = None):
        return json.dumps(self.calls, sort_keys=False, indent=indent, cls=FunctionJSONEncoder)

    def callStack(self):
        return []

    def isRoot(self):
        return True

    @staticmethod
    def fromRecord(string):
        # The record format (see: record.cpp):
        #   [optional threadid ][entering|exiting][function]
        recordRx = re.compile(r"^(?P<threadId>[^\s]*)\s?(?P<enteringExiting>entering|exiting)\s(?P<functionName>.+)\n", re.MULTILINE)

        rootFunction = CCT()
        currentFunctionByThread = {}
        for match in recordRx.finditer(string):
            threadId = match.group("threadId")
            if not threadId:
                threadId = "no thread"
            enteringExiting = match.group("enteringExiting")
            functionName = match.group("functionName")
            if enteringExiting == "entering":
                nextFunction = Function(functionName)
                if threadId not in currentFunctionByThread:
                    currentFunctionByThread[threadId] = rootFunction
                currentFunctionByThread[threadId].addCall(nextFunction)
                currentFunctionByThread[threadId] = nextFunction
            else:
                if threadId not in currentFunctionByThread:
                    raise AssertionError("Incorrect nesting found when exiting " + functionName)
                currentFunction = currentFunctionByThread[threadId]
                if currentFunction.name != functionName:
                    raise AssertionError("Incorrect nesting found when exiting " + functionName)
                currentFunctionByThread[threadId] = currentFunction.parent
        for threadId, function in currentFunctionByThread.items():
            if not function.isRoot():
                raise AssertionError("Incorrect nesting found when exiting " + function.name)
        return rootFunction

    @staticmethod
    def fromJson(string):
        decodedFunctions = json.loads(string, cls=FunctionJSONDecoder)
        cct = CCT()
        for function in decodedFunctions:
            cct.addCall(function)
        return cct

    # Use a demangler to convert mangled function names to demangled function names.
    # See c++filt: https://linux.die.net/man/1/c++filt
    # For example: _Z1Av => A().
    def demangle(self, demangler):
        mangledNames = set()
        self._collectAllUniqueCallNames(mangledNames)

        proc = subprocess.Popen(demangler, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate('\n'.join(str(e) for e in mangledNames))
        if err != "":
            raise AssertionError(err)
        demangledNames = filter(None, out.split("\n"))

        mangledCount = len(mangledNames)
        demangledCount = len(demangledNames)
        if mangledCount != demangledCount:
            raise AssertionError("Demangling failed: tried to demangle " + str(mangledCount) + " functions but " + str(demangledCount) + " were demangled.")

        demangledNameMap = {}
        for index, mangledName in enumerate(mangledNames):
            demangledNameMap[mangledName] = demangledNames[index]

        self._demangle(demangledNameMap)

class FunctionJSONEncoder(json.JSONEncoder):

    def default(self, function):
        if not isinstance(function, Function):
            return super(FunctionJSONEncoder, self).default(function)

        jsonValue = {"name": function.name}
        if len(function.calls) > 0:
            jsonValue["calls"] = []
            for call in function.calls:
                jsonValue["calls"].append(self.default(call))
        return jsonValue

class FunctionJSONDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if "name" not in obj:
            return obj
        name = obj["name"]
        function = Function(name)
        if "calls" in obj:
            for call in obj["calls"]:
                if isinstance(call, Function):
                    function.addCall(call)
        return function
