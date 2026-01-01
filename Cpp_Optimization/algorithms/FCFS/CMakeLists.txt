cmake_minimum_required(VERSION 3.5)
project(Dynamic_Scheduler)

# Set C++14 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3")

# Add include directories (using relative paths)
set(CPP_OPT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../..")
include_directories(${CPP_OPT_DIR}/function_tools)
include_directories(${CPP_OPT_DIR}/Job_Format)
include_directories(${CPP_OPT_DIR}/algorithm_executer)
# Add executable
add_executable(FCFS FCFS.cpp)

# Link math library
target_link_libraries(FCFS m)