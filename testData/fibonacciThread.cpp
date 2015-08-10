// A fibonacci program with 3 threads.
//
// This program prints the nth fibonacci number. This test program uses NUM_THREADS threads but only
// does work in thread WORK_THREAD. For simplicty and determinism, the core fibonacci algorithm is
// not actually multithreaded.
//
// Usage: ./fibonacciThread [n]

#include <cstdlib>
#include <stdio.h>
#include <thread>

static const size_t NUM_THREADS = 3;
static const size_t WORK_THREAD = 2;
static unsigned long result;

unsigned long fib(unsigned long n) {
    if (n >= 3)
        return fib(n - 1) + fib(n - 2);
    return 1;
}

unsigned long computeFibonacci(unsigned long n) {
    if (n == 0)
        return 0;
    return fib(n);
}

void computeFibonacciThreaded(unsigned long n, size_t threadId) {
    // Only do work in one thread.
    if (threadId != WORK_THREAD)
        return;
    result = computeFibonacci(n);
}

int main(int argc, char *argv[]) {
    int numArgs = argc - 1;
    if (numArgs != 1) {
        fprintf(stderr, "This program requires a single argument for the fibonacci number to compute.\n");
        return 1;
    }

    unsigned long n = atoi(argv[1]);

    std::thread threads[NUM_THREADS];
    for (size_t i = 0; i < NUM_THREADS; i++)
        threads[i] = std::thread(&computeFibonacciThreaded, n, i);

    for (size_t i = 0; i < NUM_THREADS; i++)
        threads[i].join();

    fprintf(stdout, "Fibonacci number %lu is %lu\n", n, result);
    return 0;
}
