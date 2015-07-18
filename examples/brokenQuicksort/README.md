Find the brokenQuicksort bug with CCTDB
=========

It took team N years to write the advanced brokenQuicksort program. Days before shipping, a bug was discovered and assigned to you, the new person. You don't know enough about this complex code to know where to start. This tutorial will use CCTDB (Calling Context Tree Debugging) to find the bug.

Building
---------
CCTDB doesn't require any compile-time instrumentation, so lets simply build and run the program:
```
g++ brokenQuicksort.cpp -O0 -o brokenQuicksort

./brokenQuicksort 1 6 3 9 0
0 1 3 6 9
```


The bug
---------
All you know is that there's a bug with some input:
```
./brokenQuicksort 1 6 5 9 0
0 1 9 6 5
```

Using CCTDB
--------

Naively recording the entire program can be expensive so we'll scope the recording to a specific module and function.
Use listmodules.py to output a list of modules:
```
sudo ./listmodules.py examples/brokenQuicksort/brokenQuicksort
libsystem_c.dylib
brokenQuicksort
libmacho.dylib
...
```

Use listfunctions.py to output a list of functions:
```
sudo ./listfunctions.py examples/brokenQuicksort/brokenQuicksort -m 'brokenQuicksort'
main
sort(int*, int)
partition(int*, int, int)
quicksort(int*, int, int)
swap(int*, int, int)
```

sudo is required because CCTDB uses dtrace which uses kernel-level hooks. Lets use the module 'brokenQuicksort' and the function 'sort(int*, int))'.

Lets run the program with good and bad input and compare the calling contexts:
```
sudo ./record.py -c 'examples/brokenQuicksort/brokenQuicksort 1 6 3 9 0' -m 'brokenQuicksort' -f 'sort(int*,int)' > a.json
sudo ./record.py -c 'examples/brokenQuicksort/brokenQuicksort 1 6 5 9 0' -m 'brokenQuicksort' -f 'sort(int*,int)' > b.json

./compare.py a.json b.json
b.json diverged from a.json in 1 places:
  brokenQuicksort`swap(int*, int, int) which was called by brokenQuicksort`quicksort(int*, int, int)
```

We have the culprit! Manual inspection or standard debugging techniques can be used to find out that swap was unnecessarily being called if the first number in the quicksort routine was '5'.

