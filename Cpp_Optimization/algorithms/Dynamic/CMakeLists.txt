cmake_minimum_required(VERSION 3.5)
project(Dynamic_Scheduler)

# Set C++14 standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add compiler flags for optimization and threading
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3 -pthread")

# Find Threads package (required for std::thread)
find_package(Threads REQUIRED)

# Add include directories
include_directories(/home/melowu/Work/ultimus/Cpp_Optimization/function_tools)
include_directories(/home/melowu/Work/ultimus/Cpp_Optimization/Job_Format)
include_directories(/home/melowu/Work/ultimus/Cpp_Optimization/algorithm_executer)
# Add executable
add_executable(Dynamic Dynamic.cpp)

# Link libraries
target_link_libraries(Dynamic m Threads::Threads)

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ flags: ${CMAKE_CXX_FLAGS}")