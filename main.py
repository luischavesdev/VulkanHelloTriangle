from config import *

import queue_families

import swapchain
import frame
import pipeline
import framebuffer
import commands
import sync

class Program:
    def __init__(self):
        # Throughout the code, vk stands for Vulkan

        self.program_name = "test_name"
        self.window = None 
        self.window_width = 640
        self.window_height = 480
        self.vk_instance = None  
        self.vk_surface = None
        self.physical_device = None
        self.logical_device = None
        self.queue_family_indices = None
        self.graphics_queue = None
        self.present_queue = None
        self.build_glfw_window(self.window_width, self.window_height)

        # Makes a Vulkan Instance, similar to an OpenGL Context
        self.make_instance()

        # Makes a vk_surface
        self.make_surface()

        # Gets reference to first physical device supported
        self.choose_physical_device()

        # Setting up queue indices. Store indices from first graphics and or present queue found. Queues are created along with logcal device
        self.queue_family_indices = queue_families.find_queue_families(self.physical_device, self.vk_instance, self.vk_surface)

        # Creates the logical device and associated queues
        self.create_logical_device()

        # Caching individual queues
        self.graphics_queue = vkGetDeviceQueue(self.logical_device, self.queue_family_indices.graphics_family, 0)
        self.present_queue = vkGetDeviceQueue(self.logical_device, self.queue_family_indices.present_family, 0)

        # Makes a vk logical device
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

        appInfo = VkApplicationInfo(pApplicationName = self.program_name, applicationVersion = version, pEngineName = self.program_name, engineVersion = version, apiVersion = version)
        layers = []

        #In our simple case, we only need to make sure our system supports the VK_KHR_surface extension, since GLFW will need that to create a vk_surface
        extensions = glfw.get_required_instance_extensions()

        # Get supported extensions
        supported_extensions = [extension.extensionName for extension in vkEnumerateInstanceExtensionProperties(None)]

        # Check if required extensions are in the supported list
        for extension in extensions:
            if extension not in supported_extensions:
                print("ERROR: Extension is NOT supported!")
                return None
                
        # Create info is needed for instance creation down below
        create_info = VkInstanceCreateInfo(pApplicationInfo = appInfo, enabledLayerCount = len(layers), ppEnabledLayerNames = layers, 
            enabledExtensionCount = len(extensions), ppEnabledExtensionNames = extensions)

        # Creating an instance can raise an exception
        try:
            self.vk_instance = vkCreateInstance(create_info, None)
        except:
            print("ERROR: CREATING INSTANCE!")

    def make_surface(self):
        # To create a surface from a window, we will need to use a glfw function that instead of returning the surface, stores it in a variable we pass as argument.
        c_style_pointer = ffi.new("VkSurfaceKHR*")

        # Creating and checking vk_surface
        result =  glfw.create_window_surface(self.vk_instance, self.window, None, c_style_pointer) 
        if result != VK_SUCCESS:
            print("ERROR CREATING VULKAN SURFACE!")
        
        # Storing vk_surface
        self.vk_surface = c_style_pointer[0]
    
    def choose_physical_device(self):
        # Get all available devices
        available_devices = vkEnumeratePhysicalDevices(self.vk_instance)

        # Return the first device that supports our required extension
        for device in available_devices:

            supported_extensions = [extension.extensionName for extension in vkEnumerateDeviceExtensionProperties(device, None)]

            # The only device extension we need to make sure is available is VK_KHR_SWAPCHAIN_EXTENSION_NAME
            if VK_KHR_SWAPCHAIN_EXTENSION_NAME in supported_extensions:
                self.physical_device = device
            else:
                print("ERROR: Device Extension is NOT supported!")

    def create_logical_device(self):

        # We need to make sure to create the smallest ammount of queues needed, since some family queues can be multipurpose 
        queue_create_info = []
        unique_indices = self.queue_family_indices.get_unique_indices()
        for index in unique_indices:
            queue_create_info.append(
                VkDeviceQueueCreateInfo(queueFamilyIndex = index, queueCount = 1, pQueuePriorities = [1.0,])
            )

        # Setting up the rest of the info needed to create the device
        device_features = VkPhysicalDeviceFeatures()
        enabled_layers = []
        device_extensions = [VK_KHR_SWAPCHAIN_EXTENSION_NAME]

        # Creating the info package
        create_info = VkDeviceCreateInfo(queueCreateInfoCount = len(queue_create_info), pQueueCreateInfos = queue_create_info, enabledExtensionCount = len(device_extensions), 
            ppEnabledExtensionNames = device_extensions, pEnabledFeatures = [device_features,], enabledLayerCount = len(enabled_layers), ppEnabledLayerNames = enabled_layers)

        # Finally creating the logical device
        self.logical_device = vkCreateDevice(self.physical_device, [create_info,], None)

    def make_device(self):

        bundle = swapchain.create_swapchain(
            self.vk_instance, self.logical_device, self.physical_device, self.vk_surface,
            self.window_width, self.window_height, True
        )

        self.swapchain = bundle.swapchain
        self.swapchainFrames = bundle.frames
        self.swapchainFormat = bundle.format
        self.swapchainExtent = bundle.extent

    def make_pipeline(self):

        inputBundle = pipeline.InputBundle(
            device = self.logical_device,
            swapchainImageFormat = self.swapchainFormat,
            swapchainExtent = self.swapchainExtent,
            vertexFilepath = "shaders/vert.spv",
            fragmentFilepath = "shaders/frag.spv"
        )

        outputBundle = pipeline.create_graphics_pipeline(inputBundle, True)

        self.pipelineLayout = outputBundle.pipelineLayout
        self.renderpass = outputBundle.renderPass
        self.pipeline = outputBundle.pipeline
    
    def finalize_setup(self):

        framebufferInput = framebuffer.framebufferInput()
        framebufferInput.device = self.logical_device
        framebufferInput.renderpass = self.renderpass
        framebufferInput.swapchainExtent = self.swapchainExtent
        framebuffer.make_framebuffers(
            framebufferInput, self.swapchainFrames, True
        )

        commandPoolInput = commands.commandPoolInputChunk()
        commandPoolInput.device = self.logical_device
        commandPoolInput.physicalDevice = self.physical_device
        commandPoolInput.surface = self.vk_surface
        commandPoolInput.instance = self.vk_instance
        self.commandPool = commands.make_command_pool(
            commandPoolInput, True
        )

        commandbufferInput = commands.commandbufferInputChunk()
        commandbufferInput.device = self.logical_device
        commandbufferInput.commandPool = self.commandPool
        commandbufferInput.frames = self.swapchainFrames
        self.mainCommandbuffer = commands.make_command_buffers(
            commandbufferInput, True
        )

        self.inFlightFence = sync.make_fence(self.logical_device, True)
        self.imageAvailable = sync.make_semaphore(self.logical_device, True)
        self.renderFinished = sync.make_semaphore(self.logical_device, True)

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
        vkAcquireNextImageKHR = vkGetDeviceProcAddr(self.logical_device, 'vkAcquireNextImageKHR')
        vkQueuePresentKHR = vkGetDeviceProcAddr(self.logical_device, 'vkQueuePresentKHR')

        vkWaitForFences(
            device = self.logical_device, fenceCount = 1, pFences = [self.inFlightFence,], 
            waitAll = VK_TRUE, timeout = 1000000000
        )
        vkResetFences(
            device = self.logical_device, fenceCount = 1, pFences = [self.inFlightFence,]
        )

        imageIndex = vkAcquireNextImageKHR(
            device = self.logical_device, swapchain = self.swapchain, timeout = 1000000000, 
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
                queue = self.graphics_queue, submitCount = 1, 
                pSubmits = submitInfo, fence = self.inFlightFence
            )
        except:
            print("Failed to submit draw commands")
        
        presentInfo = VkPresentInfoKHR(
            waitSemaphoreCount = 1, pWaitSemaphores = [self.renderFinished,],
            swapchainCount = 1, pSwapchains = [self.swapchain,],
            pImageIndices = [imageIndex,]
        )
        vkQueuePresentKHR(self.present_queue, presentInfo)

    def engine_close(self):

        vkDeviceWaitIdle(self.logical_device)

        
        print("ENGINE CLOSING!\n")

        vkDestroyFence(self.logical_device, self.inFlightFence, None)
        vkDestroySemaphore(self.logical_device, self.imageAvailable, None)
        vkDestroySemaphore(self.logical_device, self.renderFinished, None)

        vkDestroyCommandPool(self.logical_device, self.commandPool, None)

        vkDestroyPipeline(self.logical_device, self.pipeline, None)
        vkDestroyPipelineLayout(self.logical_device, self.pipelineLayout, None)
        vkDestroyRenderPass(self.logical_device, self.renderpass, None)
        
        for frame in self.swapchainFrames:
            vkDestroyImageView(
                device = self.logical_device, imageView = frame.image_view, pAllocator = None
            )
            vkDestroyFramebuffer(
                device = self.logical_device, framebuffer = frame.framebuffer, pAllocator = None
            )
        
        destructionFunction = vkGetDeviceProcAddr(self.logical_device, 'vkDestroySwapchainKHR')
        destructionFunction(self.logical_device, self.swapchain, None)
        vkDestroyDevice(
            device = self.logical_device, pAllocator = None
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