cmake_minimum_required(VERSION 3.28)

project(tst
    LANGUAGES CXX
)

add_executable(${CMAKE_PROJECT_NAME}
    src/main.cpp
)

find_package(ryu CONFIG REQUIRED)

target_link_libraries(${CMAKE_PROJECT_NAME}
    PRIVATE
        ryu::ryu
)
