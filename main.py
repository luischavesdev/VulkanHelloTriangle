from config import *

import device
import swapchain
import frame
import pipeline
import framebuffer
import commands
import sync

class Program:
    def __init__(self):
        # Throughout the code, vk stands for Vulkan

        # Vulkan is OS agnostic, so it works with a custom surface named vk_surface. That said, we still need a OS based window, so 
        # we use a library that will give us that type of functionality, such as GLFW for example. We'll then use vulkan's functions to create a vk_surface from 
        # the GLFW window.

        self.program_name = "test_name"
        self.window = None 
        self.window_width = 640
        self.window_height = 480
        self.vk_instance = None  
        self.vk_surface = None

        self.build_glfw_window(self.window_width, self.window_height)

        # Makes a Vulkan Instance, similar to an OpenGL Context
        self.vk_instance = self.make_instance()

        # Makes a vk_surface
        self.make_surface()

        self.make_device()
        self.make_pipeline()
        self.finalize_setup()

    def build_glfw_window(self, width, height):

        # Setting up GLFW
        glfw.init()
        glfw.window_hint(GLFW_CONSTANTS.GLFW_CLIENT_API, GLFW_CONSTANTS.GLFW_NO_API)
        glfw.window_hint(GLFW_CONSTANTS.GLFW_RESIZABLE, GLFW_CONSTANTS.GLFW_FALSE)
        
        # Creating window
        self.window = glfw.create_window(width, height, "window_test_name", None, None)
        if self.window is not None:
            print("Successfully made a glfw window called!")

    def make_instance(self):

        # Gives us a values with byte flags that indicate the most recent version of Vulkan that is supported by the system
        version = vkEnumerateInstanceVersion()

        # That said, we can just drop down to the base version to ensure compatibility
        version = VK_MAKE_VERSION(1, 1, 0)

        # App info is needed for create info down below
        appInfo = VkApplicationInfo(
            pApplicationName = self.program_name,
            applicationVersion = version,
            pEngineName = self.program_name,
            engineVersion = version,
            apiVersion = version
        )

        # Layers are a concept that Vulkan uses to provide additional functionality, mostly related to debbuging. This is done since Vulkan strives to have as little overhead as possible,
        # so if the user wants any feature, they need to explicitly state so. Since we are writting a simple program, we will choose to opt-out.
        # A similar concept is that of extensions. In this case though, for now, we only need to make sure our system supports the VK_KHR_surface, since GLFW will need that to create a
        # vk_surface
        layers = []
        # get extensions needed by GLFW
        extensions = glfw.get_required_instance_extensions()

        # Get supported extensions
        supported_extensions = [extension.extensionName for extension in vkEnumerateInstanceExtensionProperties(None)]

        # Check if required extensions are in the supported list
        for extension in extensions:
            if extension not in supported_extensions:
                print("ERROR: Extension is NOT supported!")
                return None
                
        # Create info is needed for instance creation down below
        createInfo = VkInstanceCreateInfo(pApplicationInfo = appInfo, enabledLayerCount = len(layers), ppEnabledLayerNames = layers, 
            enabledExtensionCount = len(extensions), ppEnabledExtensionNames = extensions)

        # Creating and instance can raise an exception
        try:
            return vkCreateInstance(createInfo, None)
        except:
            print("ERROR CREATING INSTANCE!")
            return None

    def make_surface(self):
        # To create a surface from a window, we will need to use a glfw function that instead of returning the surface, stores it in a variable we pass as argument.
        c_style_pointer = ffi.new("VkSurfaceKHR*")

        # Creating and checking vk_surface
        result =  glfw.create_window_surface(self.vk_instance, self.window, None, c_style_pointer) 
        if result == VK_SUCCESS:
            print("Successfully abstracted glfw's surface for vulkan")
        
        # Storing vk_surface
        self.vk_surface = c_style_pointer[0]
    
    def make_device(self):

        self.physicalDevice = device.choose_physical_device(self.vk_instance, True)
        self.device = device.create_logical_device(
            physicalDevice = self.physicalDevice, instance = self.vk_instance, 
            surface = self.vk_surface, debug = True
        )
        queues = device.get_queues(
            physicalDevice = self.physicalDevice, logicalDevice = self.device, 
            instance = self.vk_instance, surface = self.vk_surface,
            debug = True
        )
        self.graphicsQueue = queues[0]
        self.presentQueue = queues[1]
        
        bundle = swapchain.create_swapchain(
            self.vk_instance, self.device, self.physicalDevice, self.vk_surface,
            self.window_width, self.window_height, True
        )

        self.swapchain = bundle.swapchain
        self.swapchainFrames = bundle.frames
        self.swapchainFormat = bundle.format
        self.swapchainExtent = bundle.extent

    def make_pipeline(self):

        inputBundle = pipeline.InputBundle(
            device = self.device,
            swapchainImageFormat = self.swapchainFormat,
            swapchainExtent = self.swapchainExtent,
            vertexFilepath = "C:/Users/PC/Desktop/finished/shaders/vert.spv",
            fragmentFilepath = "C:/Users/PC/Desktop/finished/shaders/frag.spv"
        )

        outputBundle = pipeline.create_graphics_pipeline(inputBundle, True)

        self.pipelineLayout = outputBundle.pipelineLayout
        self.renderpass = outputBundle.renderPass
        self.pipeline = outputBundle.pipeline
    
    def finalize_setup(self):

        framebufferInput = framebuffer.framebufferInput()
        framebufferInput.device = self.device
        framebufferInput.renderpass = self.renderpass
        framebufferInput.swapchainExtent = self.swapchainExtent
        framebuffer.make_framebuffers(
            framebufferInput, self.swapchainFrames, True
        )

        commandPoolInput = commands.commandPoolInputChunk()
        commandPoolInput.device = self.device
        commandPoolInput.physicalDevice = self.physicalDevice
        commandPoolInput.surface = self.vk_surface
        commandPoolInput.instance = self.vk_instance
        self.commandPool = commands.make_command_pool(
            commandPoolInput, True
        )

        commandbufferInput = commands.commandbufferInputChunk()
        commandbufferInput.device = self.device
        commandbufferInput.commandPool = self.commandPool
        commandbufferInput.frames = self.swapchainFrames
        self.mainCommandbuffer = commands.make_command_buffers(
            commandbufferInput, True
        )

        self.inFlightFence = sync.make_fence(self.device, True)
        self.imageAvailable = sync.make_semaphore(self.device, True)
        self.renderFinished = sync.make_semaphore(self.device, True)

    def record_draw_commands(self, commandBuffer, imageIndex):

        beginInfo = VkCommandBufferBeginInfo()

        try:
            vkBeginCommandBuffer(commandBuffer, beginInfo)
        except:
            print("Failed to begin recording command buffer")
        
        renderpassInfo = VkRenderPassBeginInfo(
            renderPass = self.renderpass,
            framebuffer = self.swapchainFrames[imageIndex].framebuffer,
            renderArea = [[0,0], self.swapchainExtent]
        )
        
        clearColor = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
        renderpassInfo.clearValueCount = 1
        renderpassInfo.pClearValues = ffi.addressof(clearColor)
        
        vkCmdBeginRenderPass(commandBuffer, renderpassInfo, VK_SUBPASS_CONTENTS_INLINE)
        
        vkCmdBindPipeline(commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)
        
        vkCmdDraw(
            commandBuffer = commandBuffer, vertexCount = 3, 
            instanceCount = 1, firstVertex = 0, firstInstance = 0
        )
        
        vkCmdEndRenderPass(commandBuffer)
        
        try:
            vkEndCommandBuffer(commandBuffer)
        except:
            print("Failed to end recording command buffer")
    
    def render(self):

        #grab instance procedures
        vkAcquireNextImageKHR = vkGetDeviceProcAddr(self.device, 'vkAcquireNextImageKHR')
        vkQueuePresentKHR = vkGetDeviceProcAddr(self.device, 'vkQueuePresentKHR')

        vkWaitForFences(
            device = self.device, fenceCount = 1, pFences = [self.inFlightFence,], 
            waitAll = VK_TRUE, timeout = 1000000000
        )
        vkResetFences(
            device = self.device, fenceCount = 1, pFences = [self.inFlightFence,]
        )

        imageIndex = vkAcquireNextImageKHR(
            device = self.device, swapchain = self.swapchain, timeout = 1000000000, 
            semaphore = self.imageAvailable, fence = VK_NULL_HANDLE
        )

        commandBuffer = self.swapchainFrames[imageIndex].commandbuffer
        vkResetCommandBuffer(commandBuffer = commandBuffer, flags = 0)
        self.record_draw_commands(commandBuffer, imageIndex)

        submitInfo = VkSubmitInfo(
            waitSemaphoreCount = 1, pWaitSemaphores = [self.imageAvailable,], 
            pWaitDstStageMask=[VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,],
            commandBufferCount = 1, pCommandBuffers = [commandBuffer,], signalSemaphoreCount = 1,
            pSignalSemaphores = [self.renderFinished,]
        )

        try:
            vkQueueSubmit(
                queue = self.graphicsQueue, submitCount = 1, 
                pSubmits = submitInfo, fence = self.inFlightFence
            )
        except:
            print("Failed to submit draw commands")
        
        presentInfo = VkPresentInfoKHR(
            waitSemaphoreCount = 1, pWaitSemaphores = [self.renderFinished,],
            swapchainCount = 1, pSwapchains = [self.swapchain,],
            pImageIndices = [imageIndex,]
        )
        vkQueuePresentKHR(self.presentQueue, presentInfo)

    def engine_close(self):

        vkDeviceWaitIdle(self.device)

        
        print("ENGINE CLOSING!\n")

        vkDestroyFence(self.device, self.inFlightFence, None)
        vkDestroySemaphore(self.device, self.imageAvailable, None)
        vkDestroySemaphore(self.device, self.renderFinished, None)

        vkDestroyCommandPool(self.device, self.commandPool, None)

        vkDestroyPipeline(self.device, self.pipeline, None)
        vkDestroyPipelineLayout(self.device, self.pipelineLayout, None)
        vkDestroyRenderPass(self.device, self.renderpass, None)
        
        for frame in self.swapchainFrames:
            vkDestroyImageView(
                device = self.device, imageView = frame.image_view, pAllocator = None
            )
            vkDestroyFramebuffer(
                device = self.device, framebuffer = frame.framebuffer, pAllocator = None
            )
        
        destructionFunction = vkGetDeviceProcAddr(self.device, 'vkDestroySwapchainKHR')
        destructionFunction(self.device, self.swapchain, None)
        vkDestroyDevice(
            device = self.device, pAllocator = None
        )
        
        destructionFunction = vkGetInstanceProcAddr(self.vk_instance, "vkDestroySurfaceKHR")
        destructionFunction(self.vk_instance, self.vk_surface, None)

        vkDestroyInstance(self.vk_instance, None)

	    #terminate glfw
        glfw.terminate()

    def run(self):
        while not glfw.window_should_close(self.window):

            # Needs to be called in order to be able to interact with window buttons
            glfw.poll_events() 

            self.render()

















#MAIN ENTRY POINT   
if __name__ == "__main__":
    
    my_program = Program()

    my_program.run()
    
    # Executed when main loop that gets kicked off in run() stops
    my_program.engine_close()