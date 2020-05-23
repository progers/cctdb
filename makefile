.PHONY: tests

all: out/record.o tests

out/record.o: record.cpp
	mkdir -p out
	g++ -Wall -c record.cpp -o out/record.o

test/data/out:
	mkdir -p test/data/out

test/data/out/quicksort.o: test/data/quicksort.cpp test/data/out
	g++ -finstrument-functions -Wall -std=c++11 -O0 -fno-inline -c test/data/quicksort.cpp -o test/data/out/quicksort.o

test/data/out/quicksort: out/record.o test/data/out/quicksort.o test/data/out
	g++ out/record.o test/data/out/quicksort.o -o test/data/out/quicksort

test/data/out/fibonacciThread.o: test/data/fibonacciThread.cpp test/data/out
	g++ -finstrument-functions -Wall -std=c++11 -O0 -fno-inline -c test/data/fibonacciThread.cpp -o test/data/out/fibonacciThread.o

test/data/out/fibonacciThread: out/record.o test/data/out/fibonacciThread.o test/data/out
	g++ out/record.o test/data/out/fibonacciThread.o -o test/data/out/fibonacciThread

test/data/out/singleInstructionInline.o: test/data/singleInstructionInline.cpp test/data/out
	g++ -finstrument-functions -Wall -std=c++11 -O0 -fno-inline -c test/data/singleInstructionInline.cpp -o test/data/out/singleInstructionInline.o

test/data/out/singleInstructionInline: out/record.o test/data/out/singleInstructionInline.o test/data/out
	g++ out/record.o test/data/out/singleInstructionInline.o -o test/data/out/singleInstructionInline

test/data/out/dynamicClassDarwin.o: test/data/dynamicClassDarwin.h test/data/dynamicClassDarwin.cpp test/data/out
	g++ -finstrument-functions -Wall -std=c++11 -O0 -fno-inline -dynamiclib -flat_namespace out/record.o test/data/dynamicClassDarwin.cpp -o test/data/out/dynamicClassDarwin.o

test/data/out/dynamicLoaderDarwin.o: test/data/dynamicLoaderDarwin.cpp test/data/out
	g++ -finstrument-functions -Wall -std=c++11 -O0 -fno-inline -c test/data/dynamicLoaderDarwin.cpp -o test/data/out/dynamicLoaderDarwin.o

test/data/out/dynamicLoaderDarwin: out/record.o test/data/out/dynamicLoaderDarwin.o test/data/out/dynamicClassDarwin.o test/data/out
	g++ out/record.o test/data/out/dynamicClassDarwin.o test/data/out/dynamicLoaderDarwin.o -o test/data/out/dynamicLoaderDarwin

test/data/out/brokenQuicksort.o: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -finstrument-functions -Wall -std=c++11 -O0 -fno-inline -c examples/brokenQuicksort/brokenQuicksort.cpp -o test/data/out/brokenQuicksort.o

test/data/out/brokenQuicksort: out/record.o test/data/out/brokenQuicksort.o test/data/out
	g++ out/record.o test/data/out/brokenQuicksort.o -o test/data/out/brokenQuicksort

tests: out/record.o test/data/out/quicksort test/data/out/fibonacciThread test/data/out/singleInstructionInline test/data/out/dynamicLoaderDarwin test/data/out/brokenQuicksort
	python -m unittest discover

clean:
	rm -f out/record.o test/data/out/quicksort.o test/data/out/quicksort test/data/out/fibonacciThread.o test/data/out/fibonacciThread test/data/out/singleInstructionInline.o test/data/out/singleInstructionInline test/data/out/dynamicLoaderDarwin test/data/out/dynamicLoaderDarwin.o test/data/out/dynamicClassDarwin.o test/data/out/brokenQuicksort.o test/data/out/brokenQuicksort
