// A simple fibonacci program that stops itself on startup.
//
// This program prints the nth fibonacci number. To start
// the program, send a SIGCONT signal (kill -SIGCONT [pid])
// or just attach a debugger.
//
// Usage: ./fibonacci [n]

#include <stdio.h>
#include <cstdlib>
#include <signal.h>

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

int main(int argc, char *argv[]) {
    int numArgs = argc - 1;
    if (numArgs != 1) {
        fprintf(stderr, "This program requires a single argument for the fibonacci number to compute.\n");
        return 1;
    }

    fprintf(stdout, "Stopping process, send SIGCONT (kill -SIGCONT [pid]) to continue.\n");
    raise(SIGSTOP);

    unsigned long n = atoi(argv[1]);
    fprintf(stdout, "Fibonacci number %lu is %lu\n", n, computeFibonacci(n));
    return 0;
}
