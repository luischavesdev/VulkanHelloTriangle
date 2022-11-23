from vulkan import *

class OuputBundle:

    def __init__(self, pipeline_layout, render_pass, pipeline):

        self.pipeline_layout = pipeline_layout
        self.renderpass = render_pass
        self.pipeline = pipeline

def create_shader_module(device, filename):

    code = None
    with open(filename, 'rb') as file:
        code = file.read()

    create_info = VkShaderModuleCreateInfo(sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO, codeSize=len(code), pCode=code)
    return vkCreateShaderModule(device = device, pCreateInfo = create_info, pAllocator = None)

def create_render_pass(device, swapchain_image_format):
    
    # We will only be using a color attachement
    color_attachment = VkAttachmentDescription(format=swapchain_image_format, samples=VK_SAMPLE_COUNT_1_BIT, loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR, storeOp=VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE, stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE, initialLayout=VK_IMAGE_LAYOUT_UNDEFINED, finalLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR)

    # Ref is used by subpasses to get the info defined in color attachment up above
    color_attachment_ref = VkAttachmentReference(attachment=0, layout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)

    # Our subpass will only have a color attachment, but it may have a depth stencil attachment for example
    subpass = VkSubpassDescription(pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS, colorAttachmentCount=1, pColorAttachments=color_attachment_ref)

    # Render Pass Info. Render pass holds more info needed for the pipeline
    render_pass_info = VkRenderPassCreateInfo(sType=VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO, attachmentCount=1, pAttachments=color_attachment, subpassCount=1, pSubpasses=subpass)

    return vkCreateRenderPass(device, render_pass_info, None)

def create_graphics_pipeline(device, swapchain_image_format, swapchain_extent, vertex_filepath, fragment_filepath):

    # Vertex Input. This structure describes the format of the vertex data in case any data is passed onto the vertex shader
    vertex_input_info = VkPipelineVertexInputStateCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO, vertexBindingDescriptionCount=0, 
        vertexAttributeDescriptionCount=0)

    #Input Assembly
    input_assembly_info = VkPipelineInputAssemblyStateCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO, topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
        primitiveRestartEnable=VK_FALSE)
    
    # Vertex Shader. The module struct wraps our custom shader code
    vertex_shader_module = create_shader_module(device, vertex_filepath)
    vertex_shader_info = VkPipelineShaderStageCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, stage=VK_SHADER_STAGE_VERTEX_BIT, module=vertex_shader_module,
        pName="main")

    # Viewport. Defines how stuff gets rendered from a framebuffer 
    viewport = VkViewport(0.0, 0.0, swapchain_extent.width, swapchain_extent.height, 0.0, 1.0)
    scissor = VkRect2D([0,0], swapchain_extent)
    viewport_state_info = VkPipelineViewportStateCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO, viewportCount=1, pViewports=viewport, scissorCount=1, 
        pScissors=scissor)

    # Rasterizer. Creates the fragments
    raterizer_info = VkPipelineRasterizationStateCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO, depthClampEnable=VK_FALSE, rasterizerDiscardEnable=VK_FALSE,
        polygonMode=VK_POLYGON_MODE_FILL,lineWidth=1.0,cullMode=VK_CULL_MODE_BACK_BIT,frontFace=VK_FRONT_FACE_CLOCKWISE, depthBiasEnable=VK_FALSE)

    # Fragment Shader 
    fragment_shader_module = create_shader_module(device, fragment_filepath)
    fragment_shader_info = VkPipelineShaderStageCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, stage=VK_SHADER_STAGE_FRAGMENT_BIT, module=fragment_shader_module,
        pName="main")

    # Multisampling 
    multisampling_info = VkPipelineMultisampleStateCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO, sampleShadingEnable=VK_FALSE,
        rasterizationSamples=VK_SAMPLE_COUNT_1_BIT)

    #Color Blending. Currently disabled, but can be used to blend the color output from the fragment shader with a color already on the framebuffer.
    color_blend_attachment = VkPipelineColorBlendAttachmentState(colorWriteMask=VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT,
        blendEnable=VK_FALSE )
    color_blend_info = VkPipelineColorBlendStateCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO, logicOpEnable=VK_FALSE, attachmentCount=1, 
        pAttachments=color_blend_attachment)

    # Pipeline Layout holds info about values that can be updated at draw time
    pipeline_layout_info = VkPipelineLayoutCreateInfo(sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO, pushConstantRangeCount = 0, setLayoutCount = 0)
    pipeline_layout = vkCreatePipelineLayout(device=device, pCreateInfo=pipeline_layout_info, pAllocator=None)

    # Renderpass
    render_pass = create_render_pass(device, swapchain_image_format)

    # Creating Pipeline info
    shader_stages = [vertex_shader_info, fragment_shader_info]
    pipelineInfo = VkGraphicsPipelineCreateInfo(sType=VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,stageCount=2, pStages=shader_stages, pVertexInputState=vertex_input_info, 
        pInputAssemblyState=input_assembly_info, pViewportState=viewport_state_info, pRasterizationState=raterizer_info, pMultisampleState=multisampling_info, pDepthStencilState=None,
        pColorBlendState=color_blend_info, layout=pipeline_layout, renderPass=render_pass, subpass=0)

    # Create Pipeline
    pipeline = vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, pipelineInfo, None)[0]

    # Shader Modules are not needed anymore
    vkDestroyShaderModule(device, vertex_shader_module, None)
    vkDestroyShaderModule(device, fragment_shader_module, None)

    return OuputBundle(pipeline_layout = pipeline_layout, render_pass = render_pass, pipeline = pipeline)