Calling Context Tree Debugging
=========

Warning: This is in development and is not ready to use.

CCTDB is a debugging technique where every function call is recorded for two runs of a program and then compared to find where they differ. This approach is useful for large software projects where a failing testcase is available but it's not obvious where to start debugging.

Tutorial
---------
The first step is to find module and function symbols for some high-level entry point in the program (e.g., `main()`).
```
> ./listModules.py '[your program]'
    moduleA
    moduleB
    ...
> ./listFunctions.py '[your program]' -m 'moduleA'
    int main()
    void functionA()
    int functionB(int, char)
    ...
```

Now record every function call made within the module `moduleA` and the function `int main()`. You can also capture every function call by omitting -f and -m, or attach to existing processes with -p, etc.
```
> ./record.py -m 'moduleA' -f 'int main()' [your program] [goodargs] > good.json
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
> ./record.py -m 'moduleA' -f 'int main()' [program] [badargs] > bad.json
```

Lastly, compare the two runs.
```
> ./compare.py good.json bad.json
    good.json diverged from bad.json in 1 places:
        void thirdFunction(...) which was called by int main()
```

The bad input didn't call `thirdFunction(...)` but the good input did. Time to start debugging calls to `thirdFunction(...)`!