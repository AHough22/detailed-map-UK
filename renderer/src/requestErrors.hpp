#pragma once
#include <webgpu/webgpu_cpp.h>

extern wgpu::Adapter adapter;
void RequestAdapterError(wgpu::RequestAdapterStatus status,
                         wgpu::Adapter a,
                         wgpu::StringView message);


extern wgpu::Device device;
void RequestDeviceError(wgpu::RequestDeviceStatus status,
                        wgpu::Device d,
                        wgpu::StringView message);

void UncapturedError(const wgpu::Device&,
                     wgpu::ErrorType type,
                     wgpu::StringView message);
