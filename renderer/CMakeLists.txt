cmake_minimum_required(VERSION 4.2)

#Cmake 4.2 added support for cross-compiling with the Emscripten toolchain.
#This allows programming in C++ and compiling to WASM with javascript bindings for browser execution directly through cmake.

set(CMAKE_SYSTEM_NAME Emscripten)

project( detailed-map-UK
         VERSION 0.1.0
         LANGUAGES CXX C )

set(CMAKE_CXX_COMPILER /usr/local/bin/em++)

add_executable(App src/test.cpp)

set_target_properties(App PROPERTIES
                      SUFFIX ".html"
                      CXX_STANDARD 17
                      CXX_STANDARD_REQUIRED ON
                      CXX_EXTENSIONS OFF
                      COMPILE_WARNING_AS_ERROR ON)

target_link_options(App PRIVATE
                    -sUSE_GLFW=3
                    --use-port=emdawnwebgpu
                    -sASYNCIFY
                    )
