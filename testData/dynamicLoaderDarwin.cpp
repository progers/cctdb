// A simple program which loads and uses a dynamic library.

#include "dynamicClassDarwin.h"
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>

void notDynamicC() {
    fprintf(stderr, "notDynamicC\n");
}

int main(int argc, char *argv[]) {
    void* handle = dlopen("testData/dynamicClassDarwin.so", RTLD_LAZY);

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
