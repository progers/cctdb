Find the brokenQuicksort bug with CCTDB
=========

It took a large team 3 years to write the advanced brokenQuicksort program. Days before shipping, a bug was discovered and assigned to you, the new person. You don't know enough about this complex code to know where to start. This tutorial will use CCTDB (Calling Context Tree Debugging) to find the bug.

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

Lets start by picking a module and function to focus on: the sort() call. Use record.py to output a list of modules and functions:
```
sudo ./record.py -r 'examples/brokenQuicksort/brokenQuicksort 1 6 3 9 0' -m list -f list | grep sort\(

module(brokenQuicksort) function(quicksort(int*, int, int))
module(brokenQuicksort) function(sort(int*, int))
```
sudo is required because CCTDB uses dtrace which uses kernel-level hooks. Lets use the module brokenQuicksort and the function sort(int*, int)).

Lets run the program with good and bad input and compare the calling contexts:
```
sudo ./record.py -r 'examples/brokenQuicksort/brokenQuicksort 1 6 3 9 0' -m 'brokenQuicksort' -f 'sort(int*,int)' > a.json
sudo ./record.py -r 'examples/brokenQuicksort/brokenQuicksort 1 6 5 9 0' -m 'brokenQuicksort' -f 'sort(int*,int)' > b.json

./compare.py -a a.json -b b.json
```

After running compare.py, your browser will open with a page comparing the two runs of brokenQuicksort.
The first run we should have the following calls:
  - sort(int*, int)
  - quicksort(int*, int, int)
  - partition(int*, int, int)
  - swap(int*, int, int)
  - ...
  - quicksort(int*, int, int)
  - done

The second run is nearly identical except for one additional line:
  - sort(int*, int)
  - quicksort(int*, int, int)
  - partition(int*, int, int)
  - swap(int*, int, int)
  - ...
  - quicksort(int*, int, int)
  - swap(int*, int, int)
  - done

We have the culprit! Manual inspection or standard debugging techniques can be used to find out that swap was unnecessarily being called if the first number in the quicksort routine was '5'.

