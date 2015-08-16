// A simple program for testing complex call tree structures containing inlined functions.
//
// This should be compiled with -fno-inline to ensure only annotationed functions are inlined.
//
// Usage: ./complexInlinedTree

#include <cstdlib>
#include <signal.h>
#include <stdio.h>

void A(int&);
void inlineB(int&);
void C(int&);
void inlineD(int&);
void inlineE(int&);
void inlineF(int&);
void inlineG(int&);

__attribute__((always_inline))
inline void inlineG(int& step) {
    fprintf(stdout, "%d - G\n", step);
    if (step == 17) {
        A(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineF(int& step) {
    fprintf(stdout, "%d - F\n", step);
    if (step == 14) {
        inlineG(++step);
        return;
    }

    if (step == 16) {
        inlineG(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineE(int& step) {
    fprintf(stdout, "%d - E\n", step);
    if (step == 12) {
        A(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineD(int& step) {
    fprintf(stdout, "%d - D\n", step);
    if (step == 9) {
        inlineB(++step);
        return;
    }
}

void C(int& step) {
    fprintf(stdout, "%d - C\n", step);
    if (step == 3) {
        A(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineB(int& step) {
    fprintf(stdout, "%d - B\n", step);
    if (step == 2) {
        C(++step);
        return;
    }

    if (step == 5) {
        A(++step);
        return;
    }

    if (step == 10) {
        C(++step);
        return;
    }
}

void A(int& step) {
    fprintf(stdout, "%d - A\n", step);
    if (step == 1) {
        inlineB(++step);
        return;
    }

    if (step == 4) {
        inlineB(++step);
        return;
    }

    if (step == 8) {
        inlineD(++step);
        return;
    }
}

int main(int argc, char *argv[]) {
    int step = 0;

    // Branch 0:
    // This call should result in: A(1) -> B(2) -> C(3) -> A(4) -> B(5) -> A(6)
    A(++step); // step 1

    // Branch 1:
    // Ensure that the previous call chain "pops" back here.
    // This call should result in: A(7)
    A(++step); // step 7

    // Branch 2:
    // Test two inline calls in a row calling a non-inlined function.
    // This call should result in: A(8) -> D(9) -> B(10) -> C(11)
    A(++step); // step 8

    // Branch 3:
    // Test an inlined function calling A.
    // This call should result in: E(12) -> A(13)
    inlineE(++step); // step 12

    // Branch 4:
    // Test that an inline can call an inline and do nothing else.
    // This call should result in: F(14) -> G(15)
    inlineF(++step); // step 14

    // Branch 5:
    // Test that nested inlines can call A.
    // This call should result in: F(16) -> G(17) -> A(18)
    inlineF(++step); // step 16
    return 0;
}
