.PHONY: tests

all: examples/brokenQuicksort/brokenQuicksort tests

examples/brokenQuicksort/brokenQuicksort: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline examples/brokenQuicksort/brokenQuicksort.cpp -o examples/brokenQuicksort/brokenQuicksort

test/data/fibonacci: test/data/fibonacci.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline test/data/fibonacci.cpp -o test/data/fibonacci

test/data/quicksort: test/data/quicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline test/data/quicksort.cpp -o test/data/quicksort

test/data/optimizedQuicksort: test/data/quicksort.cpp
	g++ -g -Wall -std=c++11 -O1 -fno-inline test/data/quicksort.cpp -o test/data/optimizedQuicksort

test/data/fibonacciThread: test/data/fibonacciThread.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -O0 -fno-inline test/data/fibonacciThread.cpp -o test/data/fibonacciThread

test/data/complexInlinedTree: test/data/complexInlinedTree.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline test/data/complexInlinedTree.cpp -o test/data/complexInlinedTree

test/data/complexInlinedCases: test/data/complexInlinedCases.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline test/data/complexInlinedCases.cpp -o test/data/complexInlinedCases

test/data/singleInstructionInline: test/data/singleInstructionInline.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline test/data/singleInstructionInline.cpp -o test/data/singleInstructionInline

test/data/dynamicClassDarwin.so: test/data/dynamicClassDarwin.h test/data/dynamicClassDarwin.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline -dynamiclib -flat_namespace test/data/dynamicClassDarwin.cpp -o test/data/dynamicClassDarwin.so

test/data/dynamicLoaderDarwin: test/data/dynamicClassDarwin.h test/data/dynamicLoaderDarwin.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline test/data/dynamicLoaderDarwin.cpp -o test/data/dynamicLoaderDarwin

tests: examples/brokenQuicksort/brokenQuicksort test/data/fibonacci test/data/quicksort test/data/optimizedQuicksort test/data/fibonacciThread test/data/complexInlinedTree test/data/complexInlinedCases test/data/singleInstructionInline test/data/dynamicClassDarwin.so test/data/dynamicLoaderDarwin
	python -m unittest discover

clean:
	rm examples/brokenQuicksort/brokenQuicksort test/data/fibonacci test/data/quicksort test/data/optimizedQuicksort test/data/fibonacciThread test/data/complexInlinedTree test/data/complexInlinedCases test/data/singleInstructionInline test/data/dynamicClassDarwin.so test/data/dynamicLoaderDarwin
