#include "requestErrors.hpp"
#include <cstdio>
#include <cstdlib>

using namespace wgpu;

    void RequestAdapterError(RequestAdapterStatus status, Adapter a, StringView message){

        if(status != RequestAdapterStatus::Success){
            printf("RequestAdapter failed: %s \n", message.data);
            exit(1);
        }

        adapter = std::move(a);

    }

    void RequestDeviceError(RequestDeviceStatus status, Device d, StringView message){

        if(status != RequestDeviceStatus::Success){
            printf("RequestDevice failed: %s \n", message.data);
            exit(1);
        }

        device = std::move(d);

    }

    void UncapturedError(const Device&, ErrorType type, StringView message){

        printf("Error: %d - %s \n", static_cast<int>(type), message.data);
    }
