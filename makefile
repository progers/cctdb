.PHONY: tests

all: brokenQuicksortExample tests

brokenQuicksortExample: examples/brokenQuicksort/brokenQuicksort.cpp
	g++ -g -Wall -std=c++11 -O0 -fno-inline examples/brokenQuicksort/brokenQuicksort.cpp -o examples/brokenQuicksort/brokenQuicksort

tests:
	python -m unittest discover

clean:
	rm examples/brokenQuicksort/brokenQuicksort