cmake_minimum_required(VERSION 3.16)
project(SaiForexTesterScannerCore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(sai_scanner_core STATIC
    src/SaiScannerCore.cpp
)

target_include_directories(sai_scanner_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
