# cct.py - calling context tree
#
# A Calling Context Tree (CCT) has a single root which contains multiple calls to Functions which
# can themselves have other calls.

from collections import defaultdict
import json

class Function(object):

    def __init__(self, name):
        self.calls = []
        self.name = name
        self.parent = None
        self._callCountsByName = defaultdict(int)

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
        if (self.parent):
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

    @staticmethod
    def fromJson(string):
        decodedFunctions = json.loads(string, cls=FunctionJSONDecoder)
        cct = CCT()
        for function in decodedFunctions:
            cct.addCall(function)
        return cct

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
