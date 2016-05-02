.PHONY: tests

all: examples/brokenQuicksort/brokenQuicksort tests

examples/brokenQuicksort/brokenQuicksort: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline examples/brokenQuicksort/brokenQuicksort.cpp -o examples/brokenQuicksort/brokenQuicksort

testData/fibonacci: testData/fibonacci.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline testData/fibonacci.cpp -o testData/fibonacci

testData/quicksort: testData/quicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline testData/quicksort.cpp -o testData/quicksort

testData/fibonacciThread: testData/fibonacciThread.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -O0 -fno-inline testData/fibonacciThread.cpp -o testData/fibonacciThread

testData/complexInlinedTree: testData/complexInlinedTree.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline testData/complexInlinedTree.cpp -o testData/complexInlinedTree

testData/complexInlinedCases: testData/complexInlinedCases.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline testData/complexInlinedCases.cpp -o testData/complexInlinedCases

testData/singleInstructionInline: testData/singleInstructionInline.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline testData/singleInstructionInline.cpp -o testData/singleInstructionInline

tests: examples/brokenQuicksort/brokenQuicksort testData/fibonacci testData/quicksort testData/fibonacciThread testData/complexInlinedTree testData/complexInlinedCases testData/singleInstructionInline
	python -m unittest discover

clean:
	rm examples/brokenQuicksort/brokenQuicksort testData/fibonacci testData/quicksort testData/fibonacciThread testData/complexInlinedTree testData/complexInlinedCases testData/singleInstructionInline