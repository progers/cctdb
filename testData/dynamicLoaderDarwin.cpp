// A simple program which loads and uses a dynamic library.

#include "dynamicClassDarwin.h"
#include <dlfcn.h>
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

void notDynamicC() {
    fprintf(stderr, "notDynamicC\n");
}

int main(int argc, char *argv[]) {
    void* handle = dlopen("testData/dynamicClassDarwin.so", RTLD_LAZY);

    // Start in a stopped state to make attaching from tests easier.
    fprintf(stderr, "stopping state, to continue send SIGCONT (run \"kill -SIGCONT %d\")\n", getpid());
    (void)raise(SIGSTOP);

    DynamicClassDarwin* (*create)();
    create = (DynamicClassDarwin*(*)())dlsym(handle, "create");
    DynamicClassDarwin* dynamicClassDarwin = (DynamicClassDarwin*)create();

    dynamicClassDarwin->dynamicCallAB();

    void (*destroy)(DynamicClassDarwin*);
    destroy = (void(*)(DynamicClassDarwin*))dlsym(handle, "destroy");
    destroy(dynamicClassDarwin);

    notDynamicC();
    return 0;
}
