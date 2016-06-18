#include "dynamicClassDarwin.h"
#include <stdio.h>

extern "C" DynamicClassDarwin* create()
{
    return new DynamicClassDarwin;
}

extern "C" void destroy(DynamicClassDarwin* dynamicClassDarwin)
{
    delete dynamicClassDarwin;
}

DynamicClassDarwin::DynamicClassDarwin()
{
}

DynamicClassDarwin::~DynamicClassDarwin()
{
}

void DynamicClassDarwin::callA()
{
    fprintf(stderr, "A\n");
}

void DynamicClassDarwin::callB()
{
    fprintf(stderr, "B\n");
}

void DynamicClassDarwin::dynamicCallAB()
{
    fprintf(stderr, "dynamicCallAB\n");
    callA();
    callB();
}
