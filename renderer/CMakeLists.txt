cmake_minimum_required(VERSION 4.2)     #Cmake 4.2 added support for cross-compiling with the Emscripten toolchain.
set(CMAKE_SYSTEM_NAME Emscripten)       #This allows programming in C++ and compiling to WASM with javascript bindings for browser execution directly through cmake.

project( detailed-map-UK
         VERSION 0.1.0
         LANGUAGES CXX C )


set(CMAKE_CXX_COMPILER /usr/local/bin/em++)

add_executable(App src/wgpuRenderer.cpp
                   src/requestErrors.cpp)

target_include_directories(App PRIVATE
                           /usr/local/cellar/emscripten/4.0.22/libexec/cache/ports/emdawnwebgpu/emdawnwebgpu_pkg/webgpu/include
                           /usr/local/cellar/emscripten/4.0.22/libexec/cache/ports/emdawnwebgpu/emdawnwebgpu_pkg/webgpu_cpp/include)

set_target_properties(App PROPERTIES
                      RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/dist
                      CXX_STANDARD 20
                      CXX_STANDARD_REQUIRED ON
                      CXX_EXTENSIONS OFF
                      COMPILE_WARNING_AS_ERROR ON)

target_link_options(App PRIVATE
                    -sUSE_GLFW=3
                    --use-port=emdawnwebgpu
                    -sASYNCIFY
                    --embed-file ${CMAKE_SOURCE_DIR}/src/shader.wgsl@shader.wgsl
                    )
