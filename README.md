Calling Context Tree Debugging
=========

Warning: This is in development and is not ready to use.

CCTDB is a debugging technique where a graph of all function calls is recorded for two runs of a program and then compared to see where they differ. This has been implemented using compile-time instrumentation for recording function calls, and some simple analysis scripts for comparing recordings.

This technique is useful for large software projects where a failing testcase is available but it's not obvious where to start debugging. Many bugs in Chromium require more time debugging than implementing a fix. CCTDB can save time by methodically narrowing in on suspect code.

Tutorial
---------

The first step is to compile the `record.cpp` helper, then build the target program with `-finstrument-functions record.o`:
```
g++ -c record.cpp -o record.o
g++ -finstrument-functions record.o example_program.cpp -o example_program
```

Then record every function call for a good and bad run of the program:
```
RECORD_CCT=good_recording.txt example_program [ good args ]
RECORD_CCT=bad_recording.txt example_program [ args with bug ]
```

This will record two Calling Context Trees (CCT) which have a format like the following:
```
[thread id] enter main
[thread id] enter functionA()
[thread id] enter functionB()
[thread id] exit functionB()
[thread id] exit functionA()
[thread id] exit main
```

Finally, compare the two runs:
```
compare.py good_recording.txt bad_recording.txt
    good_recording.txt diverged from bad_recording.txt in 1 places:
        void thirdFunction(...) which was called by int main()
```

The bad input didn't call `thirdFunction(...)` but the good input did. Time to start debugging calls to `thirdFunction(...)`.

A simple walkthrough of this technique on real code is described in [examples/brokenQuicksort](examples/brokenQuicksort/README.md).
