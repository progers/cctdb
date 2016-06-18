Calling Context Tree Debugging
=========

Warning: This is in development and is not ready to use.

CCTDB is a debugging technique where every function call is recorded for two runs of a program and then compared to see where they diverge. This has been implemented as an LLDB script for recording function calls and some simple analysis scripts for comparing recordings.

This technique is useful for large software projects where a failing testcase is available but it's not obvious where to start debugging. Many bugs in Chromium end up being trivial one-line fixes where an engineer spends days finding the bug but only a few minutes fixing it. CCTDB can be used to save time by automatically narrowing in on suspect code.

Tutorial
---------
The first step is to start debugging your program with LLDB by setting a breakpoint at some high-level entry point (e.g., `main()`):
```
> lldb path/to/program
(lldb) breakpoint set --name main
(lldb) run [known-good arguments]
[breakpoint hit]
```

Now record every function call made from the function `int main()` by loading and running the `record` script:
```
(lldb) command script import path/to/recordCommand.py
The "record" command has been installed, type "help record" for more information.
(lldb) record --output good.json
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
(lldb) run [known-bad arguments]
[breakpoint hit]
(lldb) record --output bad.json
```

Finally, compare the two runs:
```
> ./compare.py good.json bad.json
    good.json diverged from bad.json in 1 places:
        void thirdFunction(...) which was called by int main()
```

The bad input didn't call `thirdFunction(...)` but the good input did. Time to start debugging calls to `thirdFunction(...)`.
