#include <cstdlib>
#include <emscripten/emscripten.h>
#include <webgpu/webgpu_cpp.h>
#include "utilities.hpp"

using namespace wgpu;

Instance instance;
Adapter  adapter;
Device   device;
Surface  surface;
TextureFormat  format;
RenderPipeline pipeline;

Buffer indexBuffer;
Buffer vertexBuffer;
uint32_t vertexCount;
uint32_t indexCount;

const uint32_t kWidth  = 800;
const uint32_t kHeight = 600;

bool InitializeBuffers(){

    BufferDescriptor vertexDesc{};
    BufferDescriptor indexDesc{};
    std::vector<float> vertexData;
    std::vector<uint16_t> indexData;

    vertexData = {
        -0.45f, 0.5f,
         0.45f, 0.5f,
         0.0f, -0.5f,

         0.47f, 0.47f,
         0.25f, 0.0f,
         0.69f, 0.0f
    };

    indexData = {
        0,1,2,
        3,4,5
    };

    vertexCount = static_cast<uint32_t>(vertexData.size()/2);
    indexCount  = static_cast<uint32_t>(indexData.size());


    vertexDesc.size  = vertexData.size() * sizeof(float);
    vertexDesc.usage = BufferUsage::CopyDst | BufferUsage::Vertex;
    vertexBuffer = device.CreateBuffer(&vertexDesc);

    device.GetQueue().WriteBuffer(vertexBuffer, 0, vertexData.data(), vertexDesc.size);

    indexDesc.size  = indexData.size() * sizeof(uint16_t);
    indexDesc.usage = BufferUsage::CopyDst | BufferUsage::Index;
    indexBuffer = device.CreateBuffer(&indexDesc);

    device.GetQueue().WriteBuffer(indexBuffer, 0, indexData.data(), indexDesc.size);
    return true;
}

bool Init(){

    InstanceDescriptor instanceDesc{};
    DeviceDescriptor   desc{};

    InstanceFeatureName enabledFeature = InstanceFeatureName::TimedWaitAny;

    instanceDesc.requiredFeatureCount = 1;
    instanceDesc.requiredFeatures = &enabledFeature;

    instance = CreateInstance(&instanceDesc);

    Future f1 = instance.RequestAdapter(nullptr, CallbackMode::WaitAnyOnly, RequestAdapterError);
    instance.WaitAny(f1, UINT64_MAX);
    desc.SetUncapturedErrorCallback(UncapturedError);
    Future f2 = adapter.RequestDevice(&desc, CallbackMode::WaitAnyOnly, RequestDeviceError);
    instance.WaitAny(f2, UINT64_MAX);

    if(!InitializeBuffers()) return false;

    return true;
}


Surface CreateWebSurface(Instance instance){

    EmscriptenSurfaceSourceCanvasHTMLSelector canvasDesc{};
    SurfaceDescriptor surfaceDesc{};

    canvasDesc.selector = "#canvas";
    surfaceDesc.nextInChain = &canvasDesc;

    return instance.CreateSurface(&surfaceDesc);
}


void ConfigureSurface(){

    SurfaceCapabilities  capabilities;
    SurfaceConfiguration config;

    // Get device capabilities and the
    // corresponding list of available formats
    surface.GetCapabilities(adapter, &capabilities);
    format = capabilities.formats[0];

    // Define Config Properties
    config.device = device;
    config.format = format;
    config.width  = kWidth;
    config.height = kHeight;

    surface.Configure(&config);
}

void CreateRenderPipeline(){

    ShaderModuleDescriptor shaderDesc{};
    ShaderSourceWGSL wgsl;
    ShaderModule shader;

    std::string shaderCode = LoadShaderFile("shader.wgsl");
    wgsl.code = shaderCode.c_str();

    shaderDesc.nextInChain = &wgsl;

    shader = device.CreateShaderModule(&shaderDesc);

    //======================================================//

    RenderPipelineDescriptor pipelineDesc{};
    ColorTargetState colorTarget{};
    FragmentState fragment{};
    VertexBufferLayout vertexBufferLayout{};
    VertexAttribute positionAttribute{};

    colorTarget.format = format;

    fragment.module = shader;
    fragment.targetCount = 1;
    fragment.targets = &colorTarget;

    positionAttribute.shaderLocation = 0;
    positionAttribute.format = VertexFormat::Float32x2;
    positionAttribute.offset = 0;

    vertexBufferLayout.attributeCount = 1;
    vertexBufferLayout.attributes = &positionAttribute;
    vertexBufferLayout.arrayStride = 2 * sizeof(float);
    vertexBufferLayout.stepMode = VertexStepMode::Vertex;

    pipelineDesc.vertex.module = shader;
    pipelineDesc.vertex.bufferCount = 1;
    pipelineDesc.vertex.buffers = &vertexBufferLayout;
    pipelineDesc.fragment = &fragment;

    pipeline = device.CreateRenderPipeline(&pipelineDesc);
}


void Render(){

    // assigns swapchain image for the renderpass to use, and assigns the pipeline and VB to use.

    RenderPassDescriptor renderpass{};
    RenderPassColorAttachment attachment{};
    SurfaceTexture surfaceTexture{};
    CommandEncoder encoder;
    RenderPassEncoder pass;
    CommandBuffer commands;

    surface.GetCurrentTexture(&surfaceTexture); //current swapchain image

    attachment.view = surfaceTexture.texture.CreateView();
    attachment.loadOp = LoadOp::Clear;
    attachment.storeOp = StoreOp::Store;

    renderpass.colorAttachmentCount = 1;
    renderpass.colorAttachments = &attachment;

    encoder = device.CreateCommandEncoder();

        pass = encoder.BeginRenderPass(&renderpass);

        pass.SetPipeline(pipeline);                                               //which pipeline to use
        pass.SetVertexBuffer(0, vertexBuffer, 0, vertexBuffer.GetSize());               //which VB to use
        pass.SetIndexBuffer(indexBuffer,IndexFormat::Uint16, 0, indexBuffer.GetSize()); //which IB to use
        pass.DrawIndexed(indexCount, 1, 0, 0, 0);
        pass.End();

        commands = encoder.Finish();

    device.GetQueue().Submit(1, &commands);
}



int main(){

    Init();

    surface = CreateWebSurface(instance);
    ConfigureSurface();
    CreateRenderPipeline();

    emscripten_set_main_loop(Render, 0, false);

    return 0;
}
