cmake_minimum_required(VERSION 3.10)
project(DistributionShift)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")

include_directories(
    ${CMAKE_SOURCE_DIR}/../../function_tools
    ${CMAKE_SOURCE_DIR}/../../Job_Format
    ${CMAKE_SOURCE_DIR}/../../algorithm_executer
)

add_executable(DistributionShift distribution_shift.cpp)
target_link_libraries(DistributionShift pthread)
