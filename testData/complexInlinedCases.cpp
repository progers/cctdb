// A simple program for testing complex inlined function calls.
//
// This should be compiled with -fno-inline to ensure only annotationed functions are inlined.
//
// Usage: ./complexInlinedCases

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
    if (step == 10) {
        A(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineF(int& step) {
    fprintf(stdout, "%d - F\n", step);
    if (step == 7) {
        inlineG(++step);
        return;
    }

    if (step == 9) {
        inlineG(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineE(int& step) {
    fprintf(stdout, "%d - E\n", step);
    if (step == 5) {
        A(++step);
        return;
    }
}

__attribute__((always_inline))
inline void inlineD(int& step) {
    fprintf(stdout, "%d - D\n", step);
    if (step == 2) {
        inlineB(++step);
        return;
    }
}

void C(int& step) {
    fprintf(stdout, "%d - C\n", step);
}

__attribute__((always_inline))
inline void inlineB(int& step) {
    fprintf(stdout, "%d - B\n", step);
    if (step == 3) {
        C(++step);
        return;
    }
}

void A(int& step) {
    fprintf(stdout, "%d - A\n", step);
    if (step == 1) {
        inlineD(++step);
        return;
    }
}

int main(int argc, char *argv[]) {
    int step = 0;

    // Branch 0:
    // Test two inline calls in a row calling a non-inlined function.
    // This call should result in: A(1) -> D(2) -> B(3) -> C(4)
    A(++step); // step 1

    // Branch 1:
    // Test an inlined function calling A.
    // This call should result in: E(5) -> A(6)
    inlineE(++step); // step 5

    // Branch 2:
    // Test that an inline can call an inline and do nothing else.
    // This call should result in: F(7) -> G(8)
    inlineF(++step); // step 7

    // Branch 3:
    // Test that nested inlines can call A.
    // This call should result in: F(9) -> G(10) -> A(11)
    inlineF(++step); // step 9
    return 0;
}
