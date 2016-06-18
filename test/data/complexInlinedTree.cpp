// A simple program for testing complex call tree structures containing inlined functions.
//
// This should be compiled with -fno-inline to ensure only annotationed functions are inlined.
//
// Usage: ./complexInlinedTree

#include <stdio.h>

void A(int&);
void inlineB(int&);
void C(int&);

__attribute__((always_inline))
inline void inlineE(int& step) {
    fprintf(stdout, "%d - E\n", step);
    if (step == 12) {
        A(++step);
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

    return 0;
}
