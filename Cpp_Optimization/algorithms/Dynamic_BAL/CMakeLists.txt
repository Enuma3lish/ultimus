cmake_minimum_required(VERSION 3.5)
project(Dynamic_BAL_Scheduler)

# Set C++14 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add compiler flags for optimization and threading
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3 -pthread")

# Find Threads package (required for std::thread)
find_package(Threads REQUIRED)

# Add include directories (using relative paths)
set(CPP_OPT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../..")
include_directories(${CPP_OPT_DIR}/function_tools)
include_directories(${CPP_OPT_DIR}/Job_Format)
include_directories(${CPP_OPT_DIR}/algorithm_executer)

# Add executable
add_executable(Dynamic_BAL Dynamic_BAL.cpp)

# Link libraries
target_link_libraries(Dynamic_BAL m Threads::Threads)

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ flags: ${CMAKE_CXX_FLAGS}")