.PHONY: tests

all: examples/brokenQuicksort/out/brokenQuicksort tests

examples/brokenQuicksort/out/brokenQuicksort: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline examples/brokenQuicksort/brokenQuicksort.cpp -o examples/brokenQuicksort/out/brokenQuicksort

test/data/out/fibonacci: test/data/fibonacci.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline test/data/fibonacci.cpp -o test/data/out/fibonacci

test/data/out/quicksort: test/data/quicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline test/data/quicksort.cpp -o test/data/out/quicksort

test/data/out/optimizedQuicksort: test/data/quicksort.cpp
	g++ -g -Wall -std=c++11 -O1 -fno-inline test/data/quicksort.cpp -o test/data/out/optimizedQuicksort

test/data/out/fibonacciThread: test/data/fibonacciThread.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -O0 -fno-inline test/data/fibonacciThread.cpp -o test/data/out/fibonacciThread

test/data/out/complexInlinedTree: test/data/complexInlinedTree.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline test/data/complexInlinedTree.cpp -o test/data/out/complexInlinedTree

test/data/out/complexInlinedCases: test/data/complexInlinedCases.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline test/data/complexInlinedCases.cpp -o test/data/out/complexInlinedCases

test/data/out/singleInstructionInline: test/data/singleInstructionInline.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline test/data/singleInstructionInline.cpp -o test/data/out/singleInstructionInline

test/data/out/dynamicClassDarwin.o: test/data/dynamicClassDarwin.h test/data/dynamicClassDarwin.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline -dynamiclib -flat_namespace test/data/dynamicClassDarwin.cpp -o test/data/out/dynamicClassDarwin.o

test/data/out/dynamicLoaderDarwin: test/data/dynamicClassDarwin.h test/data/dynamicLoaderDarwin.cpp test/data/out/dynamicClassDarwin.o
	g++ -g -Wall -std=c++11 -O0 -fno-inline test/data/dynamicLoaderDarwin.cpp -o test/data/out/dynamicLoaderDarwin

tests: examples/brokenQuicksort/out/brokenQuicksort test/data/out/fibonacci test/data/out/quicksort test/data/out/optimizedQuicksort test/data/out/fibonacciThread test/data/out/complexInlinedTree test/data/out/complexInlinedCases test/data/out/singleInstructionInline test/data/out/dynamicClassDarwin.o test/data/out/dynamicLoaderDarwin
	python -m unittest discover

clean:
	rm examples/brokenQuicksort/out/brokenQuicksort test/data/out/fibonacci test/data/out/quicksort test/data/out/optimizedQuicksort test/data/out/fibonacciThread test/data/out/complexInlinedTree test/data/out/complexInlinedCases test/data/out/singleInstructionInline test/data/out/dynamicClassDarwin.o test/data/out/dynamicLoaderDarwin
