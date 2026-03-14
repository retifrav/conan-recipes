#include <iostream>

#include <zlib/zlib.h>

#include <thingy/thingy.h>

namespace thingy
{
    void callSomethingFromZlib()
    {
        std::cout << zlibVersion() << std::endl;
    }
}
