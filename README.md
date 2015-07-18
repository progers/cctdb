Calling Context Tree Debugging
=========

This is only a proof of concept and needs more testing.

CCTDB is a debugging technique where every function call is recorded for two runs of a program and then compared to find where they differ. This approach is useful for large software projects where a failing testcase is available but it's not obvious where to start debugging.

Calling Context Trees are currently generated using dtrace which has downsides (OSX-only, requires root). I hope ptrace/gdb/lldb can be used to generate better CCTs in the future.

Tutorial
---------
The first step is to find module and function symbols for some high-level entry point in the program (e.g., `main()`).
```
> sudo ./listmodules.py '[your program]'
    moduleA
    moduleB
    ...
> sudo ./listfunctions.py '[your program]' -m 'moduleA'
    int main()
    void functionA()
    int functionB(int, char)
    ...
```

Now record every function call made within the module `moduleA` and the function `int main()`. You can also capture every function call by omitting -f and -m, or attach to existing processes with -p, etc.
```
> sudo ./record.py -c '[your program] [args]' -m 'moduleA' -f 'int main()' > goodrecording.json
```

This will record a Calling Context Tree (CCT) which has a format like the following:
```
[
    {
        "name": "int main()"
        "calls": [
            { "name": "int secondFunction(...)" },
            { "name": "void thirdFunction(...)" },
            { "name": "int secondFunction(...)" }
        ]
    }
]
```

Now record a second CCT but on a run of the program that contains a bug:
```
> sudo ./record.py -c '[your program] [badinput]' -m 'moduleA' -f 'int main()' > badrecording.json
```

Lastly, compare the two runs.
```
> ./compare.py goodrecording.json badrecording.json
    goodrecording.json diverged from badrecording.json in 1 places:
        void thirdFunction(...) which was called by int main()
```

The bad input didn't call `thirdFunction(...)` but the good input did. Time to start debugging calls to `thirdFunction(...)`!