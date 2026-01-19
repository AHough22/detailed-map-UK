#include <cstdlib>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <emscripten/emscripten.h>
#include <GLFW/glfw3.h>
#include <webgpu/webgpu_cpp.h>
#include <webgpu/webgpu_glfw.h>
#include "requestErrors.hpp"

using namespace wgpu;

Instance instance;
Adapter  adapter;
Device   device;
Surface  surface;
TextureFormat  format;
RenderPipeline pipeline;

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


const uint32_t kWidth  = 800;
const uint32_t kHeight = 600;

void ConfigureSurface(){

    SurfaceCapabilities capabilities;

    surface.GetCapabilities(adapter, &capabilities);
    format = capabilities.formats[0];

    SurfaceConfiguration config{
        .device = device,
        .format = format,
        .width  = kWidth,
        .height = kHeight
    };

    surface.Configure(&config);
}

void Init(){

    instance = CreateInstance(nullptr);

    Future f1 = instance.RequestAdapter(nullptr, CallbackMode::WaitAnyOnly, RequestAdapterError);
    instance.WaitAny(f1, UINT64_MAX);

    DeviceDescriptor desc{};
    desc.SetUncapturedErrorCallback(UncapturedError);

    Future f2 = adapter.RequestDevice(&desc, CallbackMode::WaitAnyOnly, RequestDeviceError);
    instance.WaitAny(f2, UINT64_MAX);
}


void CreateRenderPipeline(){

    std::string shaderCode = LoadShaderFile("shader.wgsl");

    ShaderSourceWGSL wgsl{};
    wgsl.code = shaderCode.c_str();

    ShaderModuleDescriptor shaderDesc{};
    shaderDesc.nextInChain = &wgsl;

    ShaderModule shader = device.CreateShaderModule(&shaderDesc);

    ColorTargetState colorTarget{ .format = format };

    FragmentState fragment{ .module      = shader,
                            .targetCount = 1,
                            .targets     = &colorTarget };

    RenderPipelineDescriptor pipelineDesc{ .vertex   = {.module = shader},
                                           .fragment = &fragment };

    pipeline = device.CreateRenderPipeline(&pipelineDesc);
}


void Render(){

    SurfaceTexture surfaceTexture;

    surface.GetCurrentTexture(&surfaceTexture);

    RenderPassColorAttachment attachment{
        .view    = surfaceTexture.texture.CreateView(),
        .loadOp  = LoadOp::Clear,
        .storeOp = StoreOp::Store
    };

    RenderPassDescriptor renderpass{
      .colorAttachmentCount = 1,
      .colorAttachments = &attachment
    };

    CommandEncoder encoder = device.CreateCommandEncoder();
    RenderPassEncoder pass = encoder.BeginRenderPass(&renderpass);
    pass.SetPipeline(pipeline);
    pass.Draw(3);
    pass.End();
    CommandBuffer commands = encoder.Finish();
    device.GetQueue().Submit(1, &commands);
}

Surface CreateWebSurface(Instance instance){
    EmscriptenSurfaceSourceCanvasHTMLSelector canvasDesc{};
    canvasDesc.selector = "#canvas";

    SurfaceDescriptor surfaceDesc{};
    surfaceDesc.nextInChain = &canvasDesc;

    return instance.CreateSurface(&surfaceDesc);
}

int main(){

    Init();

    surface = CreateWebSurface(instance);
    ConfigureSurface();
    CreateRenderPipeline();

    emscripten_set_main_loop(Render, 0, false);

    return 0;
}
