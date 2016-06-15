Find the brokenQuicksort bug with CCTDB
=========

It took years to write the advanced brokenQuicksort program. Days before shipping, a bug was discovered and assigned to you, the new person. You don't know enough about this complex code to know where to start. This tutorial will use Calling Context Tree Debugging to find the bug.

Building
---------
No compile-time instrumentation is needed so lets simply build the program:
```
> g++ -g brokenQuicksort.cpp -o brokenQuicksort
```

The bug
---------
All you know is that there's a bug with certain input:
```
> ./brokenQuicksort 1 6 3 9 0
    0 1 3 6 9 // Good
> ./brokenQuicksort 1 6 5 9 0
    0 1 9 6 5 // Bad, this is not sorted
```

Using CCTDB
--------

Begin by starting `lldb` and setting a breakpoint. Naively recording the entire program can be expensive so lets try looking for bugs below the `sort` function:
```
> lldb
(lldb) target create "examples/brokenQuicksort/brokenQuicksort"
Current executable set to 'examples/brokenQuicksort/brokenQuicksort' (x86_64).
(lldb) breakpoint set --name sort
Breakpoint 1: where = brokenQuicksort`sort(int*, int) + 17 at brokenQuicksort.cpp:44
```

Next, import the recording script, adding the full path to `command.py` if necessary:
```
(lldb) command script import command.py
The "record" command has been installed, type "help record" for more information.
```

Now lets record two runs of the program: the first which is known to work (`1 6 3 9 0`) and the second which contains a bug (`1 6 5 9 0`):
```
(lldb) run 1 6 3 9 0
...
* breakpoint hit at brokenQuicksort.cpp:44
   41   }
   42
   43   void sort(int* numbers, int count) {
-> 44       quicksort(numbers, 0, count);
   45   }
(lldb) record --output good.json
(lldb) c
Process 98681 exited with status = 0
```
```
(lldb) run 1 6 5 9 0
...
* breakpoint hit at brokenQuicksort.cpp:44
   41   }
   42
   43   void sort(int* numbers, int count) {
-> 44       quicksort(numbers, 0, count);
   45   }
(lldb) record --output bad.json
(lldb) quit
```

Finally, use the `compare.py` script to compare the two recordings:
```
> ./compare.py good.json bad.json
    bad.json diverged from good.json in 1 places:
        brokenQuicksort`swap(int*, int, int) which was called by brokenQuicksort`quicksort(int*, int, int)
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
