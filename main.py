from vulkan import *

import glfw
import glfw.GLFW as GLFW_CONSTANTS

import queue_families
import swapchain
import pipeline

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
        self.swapchain_bundle = None
        self.pipeline_bundle = None
        self.command_pool = None
        self.main_commandbuffer = None
        self.image_available_semaphore = None
        self.render_finished_semaphore = None
        self.build_glfw_window(self.window_width, self.window_height)

        # Makes a Vulkan Instance, similar to an OpenGL Context
        self.make_instance()

        # Makes a vk_surface
        self.make_surface()

        # Gets reference to first physical device supported
        self.choose_physical_device()

        # Setting up queue indices. Store indices from first graphics and or present queue found. Queues are created along with logical device
        self.queue_family_indices = queue_families.find_queue_families(self.physical_device, self.vk_instance, self.vk_surface)

        # Creates the logical device and associated queues
        self.create_logical_device()

        # Caching individual queues
        self.graphics_queue = vkGetDeviceQueue(self.logical_device, self.queue_family_indices.graphics_family, 0)
        self.present_queue = vkGetDeviceQueue(self.logical_device, self.queue_family_indices.present_family, 0)

        # Makes a swapchain
        self.swapchain_bundle = swapchain.create_swapchain(self.vk_instance, self.logical_device, self.physical_device, self.vk_surface, self.window_width, 
            self.window_height, self.queue_family_indices)

        # Makes a pipeline
        self.pipeline_bundle = pipeline.create_graphics_pipeline(self.logical_device, self.swapchain_bundle.color_format.format, self.swapchain_bundle.extent, 
            "shaders/vert.spv", "shaders/frag.spv")

        # Populates swapchain_bundle.frames with framebuffers
        self.create_framebuffers()

        # Creates commandbuffers and related structures
        self.create_commandbuffers()

        # Creates obejcts that are needed to control the flow of execution, either between GPU and CPU, or just CPU
        self.create_sync_objects()

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
    
    def create_framebuffers(self):

        for i, frame in enumerate(self.swapchain_bundle.frames):
            attachments = [frame.image_view]
            framebufferInfo = VkFramebufferCreateInfo(sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO, renderPass=self.pipeline_bundle.renderpass, attachmentCount=1, 
                pAttachments=attachments, width=self.swapchain_bundle.extent.width, height=self.swapchain_bundle.extent.height,layers=1)

            try:
                frame.framebuffer = vkCreateFramebuffer(self.logical_device, framebufferInfo, None)
            except:
                print("ERROR: making Framebuffer!")

    def create_commandbuffers(self):
        # Command Pool
        pool_info = VkCommandPoolCreateInfo(self.queue_family_indices.graphics_family, flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT)
        try:
            self.command_pool = vkCreateCommandPool(self.logical_device, pool_info, None)
        except:
            print("ERROR:Failed to create command pool")
            return 

        # Command Buffers
        allocInfo = VkCommandBufferAllocateInfo(commandPool = self.command_pool, level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, commandBufferCount = 1)
        # for each frame
        for i,frame in enumerate(self.swapchain_bundle.frames):

            try:
                frame.commandbuffer = vkAllocateCommandBuffers(self.logical_device, allocInfo)[0]
            except:
                print("ERROR: Failed to allocate command buffer for frame")

        # main
        try:
            self.main_commandbuffer = vkAllocateCommandBuffers(self.logical_device, allocInfo)[0]
            
        except:
            print("ERROR: Failed to allocate main command buffer")

    def create_sync_objects(self):

        # Semaphores
        semaphore_info = VkSemaphoreCreateInfo()
        try:
            self.image_available_semaphore = vkCreateSemaphore(self.logical_device, semaphore_info, None)
            self.render_finished_semaphore = vkCreateSemaphore(self.logical_device, semaphore_info, None)
        except:
            print("Failed to create semaphore")
        
        # Fence
        fence_info = VkFenceCreateInfo(flags = VK_FENCE_CREATE_SIGNALED_BIT)
        try:
            self.in_flight_fence =  vkCreateFence(self.logical_device, fence_info, None)
        except:
            print("Failed to create fence")

    def record_draw_commands(self, command_buffer, image_index):

        begin_info = VkCommandBufferBeginInfo()

        try:
            vkBeginCommandBuffer(command_buffer, begin_info)
        except:
            print("Failed to begin recording command buffer")
        
        renderpass_info = VkRenderPassBeginInfo(renderPass = self.pipeline_bundle.renderpass, framebuffer = self.swapchain_bundle.frames[image_index].framebuffer, 
            renderArea = [[0,0], self.swapchain_bundle.extent])
        
        clear_color = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
        renderpass_info.clearValueCount = 1
        renderpass_info.pClearValues = ffi.addressof(clear_color)
        
        vkCmdBeginRenderPass(command_buffer, renderpass_info, VK_SUBPASS_CONTENTS_INLINE)
        vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline_bundle.pipeline)
        vkCmdDraw(commandBuffer = command_buffer, vertexCount = 3, instanceCount = 1, firstVertex = 0, firstInstance = 0)
        vkCmdEndRenderPass(command_buffer)
        
        try:
            vkEndCommandBuffer(command_buffer)
        except:
            print("Failed to end recording command buffer")
    
    def render(self):

        vkWaitForFences(device = self.logical_device, fenceCount = 1, pFences = [self.in_flight_fence,], waitAll = VK_TRUE, timeout = 1000000000)
        vkResetFences(device = self.logical_device, fenceCount = 1, pFences = [self.in_flight_fence,])

        # Get next image 
        vkAcquireNextImageKHR = vkGetDeviceProcAddr(self.logical_device, 'vkAcquireNextImageKHR')
        image_index = vkAcquireNextImageKHR(device = self.logical_device, swapchain = self.swapchain_bundle.swapchain, timeout = 1000000000, semaphore = self.image_available_semaphore, 
            fence = VK_NULL_HANDLE)

        # Setup command buffer from intended swapchain image
        command_buffer = self.swapchain_bundle.frames[image_index].commandbuffer
        vkResetCommandBuffer(commandBuffer = command_buffer, flags = 0)

        # Record Draw Command
        self.record_draw_commands(command_buffer, image_index)

        # Submit command to queue
        submit_info = VkSubmitInfo(waitSemaphoreCount = 1, pWaitSemaphores = [self.image_available_semaphore,], pWaitDstStageMask=[VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,],
            commandBufferCount = 1, pCommandBuffers = [command_buffer,], signalSemaphoreCount = 1, pSignalSemaphores = [self.render_finished_semaphore,])
        try:
            vkQueueSubmit(queue = self.graphics_queue, submitCount = 1, pSubmits = submit_info, fence = self.in_flight_fence)
        except:
            print("Failed to submit draw commands")
        
        # Present
        present_info = VkPresentInfoKHR(waitSemaphoreCount = 1, pWaitSemaphores = [self.render_finished_semaphore,], swapchainCount = 1, pSwapchains = [self.swapchain_bundle.swapchain,],
            pImageIndices = [image_index,])
        vkQueuePresentKHR = vkGetDeviceProcAddr(self.logical_device, 'vkQueuePresentKHR')
        vkQueuePresentKHR(self.present_queue, present_info)

    def engine_close(self):

        # Wait for processes that may still be running, before freeing up memory
        vkDeviceWaitIdle(self.logical_device)

        print("ENGINE CLOSING!")

        vkDestroyFence(self.logical_device, self.in_flight_fence, None)
        vkDestroySemaphore(self.logical_device, self.image_available_semaphore, None)
        vkDestroySemaphore(self.logical_device, self.render_finished_semaphore, None)

        vkDestroyCommandPool(self.logical_device, self.command_pool, None)

        vkDestroyPipeline(self.logical_device, self.pipeline_bundle.pipeline, None)
        vkDestroyPipelineLayout(self.logical_device, self.pipeline_bundle.pipeline_layout, None)
        vkDestroyRenderPass(self.logical_device, self.pipeline_bundle.renderpass, None)
        
        for frame in self.swapchain_bundle.frames:
            vkDestroyImageView(
                device = self.logical_device, imageView = frame.image_view, pAllocator = None
            )
            vkDestroyFramebuffer(
                device = self.logical_device, framebuffer = frame.framebuffer, pAllocator = None
            )
        
        DestroySwapchain = vkGetDeviceProcAddr(self.logical_device, 'vkDestroySwapchainKHR')
        DestroySwapchain(self.logical_device, self.swapchain_bundle.swapchain, None)

        vkDestroyDevice(device = self.logical_device, pAllocator = None)
        
        DestroySurface = vkGetInstanceProcAddr(self.vk_instance, "vkDestroySurfaceKHR")
        DestroySurface(self.vk_instance, self.vk_surface, None)

        vkDestroyInstance(self.vk_instance, None)

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