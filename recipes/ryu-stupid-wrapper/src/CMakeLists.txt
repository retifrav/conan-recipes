cmake_minimum_required(VERSION 3.28)

set(THINGY_VERSION "0.0.0" CACHE STRING "Thingy version")

set(PROJECT_NAMESPACE "some")
project("thingy"
    VERSION ${THINGY_VERSION}
    DESCRIPTION "Some thingy"
)

set(REQUIRED_CPP_STANDARD 17 CACHE STRING "Required C++ standard")
if(DEFINED CMAKE_CXX_STANDARD)
    if(CMAKE_CXX_STANDARD LESS ${REQUIRED_CPP_STANDARD})
        message(FATAL_ERROR "This project requires at least C++${REQUIRED_CPP_STANDARD}")
    endif()
else()
    set(CMAKE_CXX_STANDARD ${REQUIRED_CPP_STANDARD})
endif()
set(CMAKE_CXX_STANDARD_REQUIRED YES)
if(NOT DEFINED CMAKE_CXX_EXTENSIONS)
    set(CMAKE_CXX_EXTENSIONS NO)
endif()

# global debug postfix for libraries (executables still need to set it)
set(CMAKE_DEBUG_POSTFIX "d" CACHE STRING "Filename postfix for libraries under DEBUG configuration")

add_library(${PROJECT_NAME})
# not really required, package will get the namespace via `install(EXPORT ...)`
add_library("${PROJECT_NAMESPACE}::${PROJECT_NAME}" ALIAS ${PROJECT_NAME})

include(GenerateExportHeader)
generate_export_header(${PROJECT_NAME}
    EXPORT_FILE_NAME "${PROJECT_NAME}/export.h"
)

target_sources(${PROJECT_NAME}
    PRIVATE
        src/thingy.cpp
    PUBLIC
        FILE_SET public_headers
            TYPE HEADERS
            BASE_DIRS include
            FILES
                include/thingy/thingy.h
        FILE_SET generated_headers
            TYPE HEADERS
            BASE_DIRS $<TARGET_PROPERTY:${PROJECT_NAME},BINARY_DIR>
            FILES
                ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}/export.h
)

target_include_directories(${PROJECT_NAME}
    PRIVATE
        # where the library itself will look for its internal headers
        ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}
    PUBLIC
        # where top-level project will look for the library's public headers
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        # where external projects will look for the library's public headers
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_${REQUIRED_CPP_STANDARD}")

find_package(ryu CONFIG REQUIRED)

target_link_libraries(${PROJECT_NAME}
    PRIVATE
        ryu::ryu
)

include(Installing.cmake)
