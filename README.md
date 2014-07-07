Calling Context Tree Debugging
=========

CCTDB is a debugging technique where every function call is recorded for two runs of a program and then compared to find where they differ. This approach is useful for large software projects where a failing testcase is available but it's not obvious where to start debugging.

The program does not need to be compiled with special flags or instrumentation as function calls are traced at the kernel level (requires sudo) using dtrace.

CCTDB is practical for projects as large as Chromium. At the moment, the code is quite fragile (only works on OSX, if at all, etc).

Requirements
---------
  - dtrace and root access for kernel tracing.

Tutorial
---------
This is a short walkthrough and there are more detailed examples in the examples folder.

The first step is to find module and function symbols for some high-level entry point in the program (e.g., main()).
```
sudo ./record.py -r '[your program]' -m list -f list

module(modulea) function(main())
module(moduleb) function(foo(int*))
...
```

We want CCTDB to trace every function call made within main(), and separate groups of function calls if main() is called multiple times.
```
sudo ./record.py -r '[your program]' -m 'modulea' -f 'main()'
```

This will launch your program and trace all function calls in main(), outputting the result as json. You can also capture every function call by omitting -f, attach to existing processes with -p, etc.

Our goal is to find the difference between two program runs. Use CCTDB to run the program twice, once with known good input and a second time with the bug:
```
sudo ./record.py -r '[your program] goodInput' -m 'modulea' -f 'main()' > good.json
sudo ./record.py -r '[your program] badInput' -m 'modulea' -f 'main()' > bad.json

./compare.py -a good.json -b bad.json
```
The compare call will open your default browser with a diff viewer showing where the two runs differed.
