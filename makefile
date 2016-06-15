.PHONY: tests

all: examples/brokenQuicksort/brokenQuicksort tests

examples/brokenQuicksort/brokenQuicksort: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline examples/brokenQuicksort/brokenQuicksort.cpp -o examples/brokenQuicksort/brokenQuicksort

testData/fibonacci: testData/fibonacci.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline testData/fibonacci.cpp -o testData/fibonacci

testData/quicksort: testData/quicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline testData/quicksort.cpp -o testData/quicksort

testData/optimizedQuicksort: testData/quicksort.cpp
	g++ -g -Wall -std=c++11 -O1 -fno-inline testData/quicksort.cpp -o testData/optimizedQuicksort

testData/fibonacciThread: testData/fibonacciThread.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -O0 -fno-inline testData/fibonacciThread.cpp -o testData/fibonacciThread

testData/complexInlinedTree: testData/complexInlinedTree.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline testData/complexInlinedTree.cpp -o testData/complexInlinedTree

testData/complexInlinedCases: testData/complexInlinedCases.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline testData/complexInlinedCases.cpp -o testData/complexInlinedCases

testData/singleInstructionInline: testData/singleInstructionInline.cpp
	g++ -g -Wall -std=c++11 -stdlib=libc++ -fno-inline testData/singleInstructionInline.cpp -o testData/singleInstructionInline

testData/dynamicClassDarwin.so: testData/dynamicClassDarwin.h testData/dynamicClassDarwin.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline -dynamiclib -flat_namespace testData/dynamicClassDarwin.cpp -o testData/dynamicClassDarwin.so

testData/dynamicLoaderDarwin: testData/dynamicClassDarwin.h testData/dynamicLoaderDarwin.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline testData/dynamicLoaderDarwin.cpp -o testData/dynamicLoaderDarwin

tests: examples/brokenQuicksort/brokenQuicksort testData/fibonacci testData/quicksort testData/optimizedQuicksort testData/fibonacciThread testData/complexInlinedTree testData/complexInlinedCases testData/singleInstructionInline testData/dynamicClassDarwin.so testData/dynamicLoaderDarwin
	python -m unittest discover

clean:
	rm examples/brokenQuicksort/brokenQuicksort testData/fibonacci testData/quicksort testData/optimizedQuicksort testData/fibonacciThread testData/complexInlinedTree testData/complexInlinedCases testData/singleInstructionInline testData/dynamicClassDarwin.so testData/dynamicLoaderDarwin testData/integrationTestOutputGood.json testData/integrationTestOutputBad.json
