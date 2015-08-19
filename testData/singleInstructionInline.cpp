// A simple program for testing inlines with a single instruction.
//
// This should be compiled with -fno-inline to ensure only annotationed functions are inlined.
//
// Usage: ./singleInstructionInline

#include <stdio.h>

void A();
void inlineB();
void C();
void D();

void D() {
    fprintf(stdout, "D\n");
}

void C() {
    D();
}

__attribute__((always_inline))
inline void inlineB() {
    C();
}

void A() {
    fprintf(stdout, "A\n");
    inlineB();
}

int main(int argc, char *argv[]) {
    A();
    return 0;
}
