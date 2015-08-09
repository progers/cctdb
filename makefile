.PHONY: tests

all: examples/brokenQuicksort/brokenQuicksort testData/fibonacci tests

examples/brokenQuicksort/brokenQuicksort: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline examples/brokenQuicksort/brokenQuicksort.cpp -o examples/brokenQuicksort/brokenQuicksort

testData/fibonacci: testData/fibonacci.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline testData/fibonacci.cpp -o testData/fibonacci

tests: examples/brokenQuicksort/brokenQuicksort testData/fibonacci
	python -m unittest discover

clean:
	rm examples/brokenQuicksort/brokenQuicksort testData/fibonacci