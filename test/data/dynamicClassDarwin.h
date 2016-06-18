#ifndef __DYNAMICCLASSDARWIN_H__
#define __DYNAMICCLASSDARWIN_H__

class DynamicClassDarwin
{
public:
    DynamicClassDarwin();
    virtual ~DynamicClassDarwin();

    virtual void dynamicCallAB();
private:
    void callA();
    void callB();
};

#endif // __DYNAMICCLASSDARWIN_H__
