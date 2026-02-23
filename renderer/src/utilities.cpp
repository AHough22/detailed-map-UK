#include "utilities.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>

using namespace wgpu;

    void RequestAdapterError(RequestAdapterStatus status, Adapter a, StringView message){
        if(status != RequestAdapterStatus::Success){ printf("RequestAdapter failed: %s \n", message.data);
                                                     exit(1); }
        adapter = std::move(a);
    }




    void RequestDeviceError(RequestDeviceStatus status, Device d, StringView message){
        if(status != RequestDeviceStatus::Success){ printf("RequestDevice failed: %s \n", message.data);
                                                    exit(1); }
        device = std::move(d);
    }




    void UncapturedError(const Device&, ErrorType type, StringView message){
        printf("Error: %d - %s \n", static_cast<int>(type), message.data);
    }


    std::string LoadShaderFile(const char* path){
        std::ifstream file(path);
        if(!file.is_open()){
            printf("Failed to open shader file: %s\n", path);
            exit(1);
        }
        std::stringstream buffer;
        buffer << file.rdbuf();
        return buffer.str();
    }
