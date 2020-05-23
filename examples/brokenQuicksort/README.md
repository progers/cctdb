Find the brokenQuicksort bug with CCTDB
=========

It took years to write the advanced brokenQuicksort program. Days before shipping, a bug was discovered and assigned to you, the new person. You don't know enough about this complex code to know where to start. This tutorial will use Calling Context Tree Debugging to find the bug.

Building
---------
We need to build the program with instrumentation to record all function calls. Start in the project directory:
```
cd examples/brokenQuicksort
```

Build the `record` helper, setting `CCT_DIR` to the directory containing `record.cpp`:
```
CCT_DIR=../../
mkdir -p ${CCT_DIR}/out
g++ -c ${CCT_DIR}/record.cpp -o ${CCT_DIR}/out/record.o
```

Build the `brokenQuicksort` program with `-finstrument-functions` and the `record.o` helper:
```
g++ -finstrument-functions ${CCT_DIR}/out/record.o brokenQuicksort.cpp -o out/brokenQuicksort
```

The bug
---------
All you know is that there's a bug with certain input:
```
out/brokenQuicksort 1 6 3 9 0
    0 1 3 6 9 // Amazingly sorted
out/brokenQuicksort 1 6 5 9 0
    0 1 9 6 5 // This is not sorted
```

Using CCTDB
--------

By default, the instrumented program works as normal. If the `RECORD_CCT` environmental variable is present, it will be used as the filename to store a recording of all function calls.

Record two runs of the program: the first which is known to work (`1 6 3 9 0`) and the second which contains a bug (`1 6 5 9 0`).
```
RECORD_CCT=out/good.txt out/brokenQuicksort 1 6 3 9 0
    0 1 3 6 9

RECORD_CCT=out/bad.txt out/brokenQuicksort 1 6 5 9 0
    0 1 9 6 5
```

Finally, use the `compare.py` script to compare the two recordings:
```
python ${CCT_DIR}/compare.py out/good.txt out/bad.txt
    bad.txt diverged from good.txt in 1 places:
        swap(int*, int, int) which was called by quicksort(int*, int, int)
```

We have the culprit! Manual inspection or standard debugging techniques can now be used starting in `quicksort` and looking for a bad call to `swap`.
```
   33   void quicksort(int* numbers, int a, int b) {
   34       if (a < b) {
   35           int m = partition(numbers, a, b);
   36           quicksort(numbers, a, m - 1);
   37           quicksort(numbers, m + 1, b);
   38           if (numbers[a] == 5) // FIXME: What is this doing here?
-> 39               swap(numbers, a, b);
   40       }
   41   }
```

Using CCTDB we were able to zero in on the bug quickly and find that line `38` and `39` should just be deleted.
