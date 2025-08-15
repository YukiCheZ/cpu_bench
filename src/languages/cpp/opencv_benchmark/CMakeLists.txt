cmake_minimum_required(VERSION 3.10)
project(CPU_OpenCV_Benchmark)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# -----------------------------
# 用户选择编译器
# -----------------------------
set(ALLOWED_COMPILERS gcc clang)
set(COMPILER "gcc" CACHE STRING "Choose compiler: gcc or clang")

if(NOT COMPILER IN_LIST ALLOWED_COMPILERS)
    message(FATAL_ERROR "Invalid compiler choice. Options are: gcc, clang")
endif()

if(COMPILER STREQUAL "gcc")
    find_program(GCC_CXX g++)
    if(NOT GCC_CXX)
        message(FATAL_ERROR "GCC compiler not found!")
    endif()
    set(CMAKE_CXX_COMPILER ${GCC_CXX})
elseif(COMPILER STREQUAL "clang")
    find_program(CLANG_CXX clang++)
    if(NOT CLANG_CXX)
        message(FATAL_ERROR "Clang compiler not found!")
    endif()
    set(CMAKE_CXX_COMPILER ${CLANG_CXX})
endif()

# -----------------------------
# 用户选择优化等级
# -----------------------------
set(ALLOWED_OPT O1 O2 O3)
set(BUILD_OPT O2 CACHE STRING "Build optimization: O1, O2, O3")

if(NOT BUILD_OPT IN_LIST ALLOWED_OPT)
    message(FATAL_ERROR "Invalid optimization option. Choose from O1, O2, O3")
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -${BUILD_OPT}")

# -----------------------------
# Conda 环境支持
# -----------------------------
if(DEFINED ENV{CONDA_PREFIX})
    list(APPEND CMAKE_PREFIX_PATH $ENV{CONDA_PREFIX})
endif()

# -----------------------------
# 查找 OpenCV
# -----------------------------
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

# -----------------------------
# 可执行文件
# -----------------------------
add_executable(cpu_benchmark
    src/main.cpp
    src/data_manager.cpp
    src/workloads.cpp
)

target_link_libraries(cpu_benchmark ${OpenCV_LIBS})

# -----------------------------
# 编译器版本宏定义（安全）
# -----------------------------
execute_process(
    COMMAND ${CMAKE_CXX_COMPILER} --version
    OUTPUT_VARIABLE DETECTED_COMPILER_VERSION
    ERROR_VARIABLE _unused
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
# 去掉换行
string(REPLACE "\n" " " DETECTED_COMPILER_VERSION "${DETECTED_COMPILER_VERSION}")
# 替换内部双引号为单引号
string(REPLACE "\"" "'" DETECTED_COMPILER_VERSION "${DETECTED_COMPILER_VERSION}")
# 外层用合法双引号包裹
set(QUOTE "\"")
target_compile_definitions(cpu_benchmark PRIVATE COMPILER_VERSION_STR=${QUOTE}${DETECTED_COMPILER_VERSION}${QUOTE})

# -----------------------------
# 信息输出
# -----------------------------
message(STATUS "Selected compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Optimization level: -${BUILD_OPT}")
message(STATUS "OpenCV Include Dirs: ${OpenCV_INCLUDE_DIRS}")
message(STATUS "OpenCV Libraries: ${OpenCV_LIBS}")
message(STATUS "Using OpenCV version: ${OpenCV_VERSION}")
