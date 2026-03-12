#include <iostream>
#include <ryu/ryu.h>

int main(int argc, char *argv[])
{
    char r[128];
    const double v = 12.3456;
    int l = d2fixed_buffered_n(v, 3, r);
    std::cout << "length: " << l << std::endl
              << "result: " << r << std::endl;

    return 0;
}
