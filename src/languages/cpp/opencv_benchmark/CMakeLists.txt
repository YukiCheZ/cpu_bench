cmake_minimum_required(VERSION 3.10)
project(CPU_OpenCV_Benchmark)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 如果用户在 Conda 环境下，自动使用 $CONDA_PREFIX
if(DEFINED ENV{CONDA_PREFIX})
    list(APPEND CMAKE_PREFIX_PATH $ENV{CONDA_PREFIX})
endif()

# 查找 OpenCV
find_package(OpenCV REQUIRED)

# 包含头文件目录
include_directories(${OpenCV_INCLUDE_DIRS})

# 源文件
add_executable(cpu_benchmark src/cpu_benchmark.cpp)

# 链接 OpenCV 库
target_link_libraries(cpu_benchmark ${OpenCV_LIBS})

# 打印调试信息
message(STATUS "OpenCV Include Dirs: ${OpenCV_INCLUDE_DIRS}")
message(STATUS "OpenCV Libraries: ${OpenCV_LIBS}")
message(STATUS "Using OpenCV version: ${OpenCV_VERSION}")
