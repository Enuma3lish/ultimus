cmake_minimum_required(VERSION 3.5)
project(Dynamic_Scheduler)

# Set C++14 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3")

# Add include directories
include_directories(/Users/melowu/Desktop/ultimus/Cpp_Optimization/function_tools)
include_directories(/Users/melowu/Desktop/ultimus/Cpp_Optimization/Job_Format)
include_directories(/Users/melowu/Desktop/ultimus/Cpp_Optimization/algorithm_executer)
# Add executable
add_executable(SRPT SRPT.cpp)

# Link math library
target_link_libraries(SRPT m)