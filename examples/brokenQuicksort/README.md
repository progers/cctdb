Find the brokenQuicksort bug with CCTDB
=========

It took years to write the advanced brokenQuicksort program. Days before shipping, a bug was discovered and assigned to you, the new person. You don't know enough about this complex code to know where to start. This tutorial will use Calling Context Tree Debugging to find the bug.

Building
---------
No compile-time instrumentation is needed so lets simply build and run the program:
```
> g++ -g brokenQuicksort.cpp -o brokenQuicksort

> ./brokenQuicksort 1 6 3 9 0
    0 1 3 6 9
```


The bug
---------
All you know is that there's a bug with some input:
```
> ./brokenQuicksort 1 6 5 9 0
    0 1 9 6 5
```

Using CCTDB
--------

Naively recording the entire program can be expensive so we'll scope the recording to a specific module and function.
Use `listmodules.py` to output a list of modules:
```
> ./listmodules.py examples/brokenQuicksort/brokenQuicksort
    libsystem_c.dylib
    brokenQuicksort
    libmacho.dylib
    ...
```

Use `listfunctions.py` to output a list of functions within our module `brokenQuicksort`:
```
> ./listfunctions.py examples/brokenQuicksort/brokenQuicksort -m 'brokenQuicksort'
    main
    sort(int*, int)
    partition(int*, int, int)
    quicksort(int*, int, int)
    swap(int*, int, int)
```

Lets use the module `brokenQuicksort` and the function `sort(int*, int))` to compare two runs:
```
> ./record.py -m 'brokenQuicksort' -f 'sort(int*,int)' [path]/brokenQuicksort 1 6 3 9 0 > good.json
> ./record.py -m 'brokenQuicksort' -f 'sort(int*,int)' [path]/brokenQuicksort 1 6 5 9 0 > bad.json

> ./compare.py good.json bad.json
    bad.json diverged from good.json in 1 places:
        brokenQuicksort`swap(int*, int, int) which was called by brokenQuicksort`quicksort(int*, int, int)
```

We have the culprit! Manual inspection or standard debugging techniques can be used to find out that swap was unnecessarily being called if the first number in the quicksort routine was '5'.