// A fibonacci program with [NUM_THREADS] threads.
//
// This program computes the nth fibonacci number multiple times, each in a different thread. For
// simplicity and determinism, the core algorithm is not multithreaded. The results of the duplicated
// work are checked before returning the result.
//
// Usage: ./fibonacciThread [n]

#include <cstdlib>
#include <stdio.h>
#include <thread>

static const size_t NUM_THREADS = 3;
static unsigned long results[NUM_THREADS];

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

void computeFibonacciUsingJustOneThread(unsigned long n, size_t threadId) {
    results[threadId] = computeFibonacci(n);
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
        threads[i] = std::thread(&computeFibonacciUsingJustOneThread, n, i);
    for (size_t i = 0; i < NUM_THREADS; i++)
        threads[i].join();

    for (size_t i = 1; i < NUM_THREADS; i++) {
        if (results[0] != results[i]) {
            fprintf(stderr, "Error: threads do not agree in their fibonacci result\n");
            return 1;
        }
    }

    fprintf(stdout, "Fibonacci number %lu is %lu\n", n, results[0]);
    return 0;
}
