from vulkan import *

class SwapChainFrame:

    def __init__(self):
        
        self.image = None
        self.image_view = None
        self.frame_buffer = None
        self.command_buffer = None

class SwapChainBundle:

    def __init__(self):
        
        self.swapchain = None
        self.frames = [] # Populated with SwapChainFrames
        self.color_format = None # Color format space
        self.extent = None # Frame sizes
        self.present_mode = None # Mode to present images, such as mailbox or fifo
        self.surface_capabilities = None

def create_swapchain(instance, logicalDevice, physicalDevice, surface, width, height, queue_indices):

    my_bundle = SwapChainBundle()

    # Store surface capabilities
    vkGetPhysicalDeviceSurfaceCapabilitiesKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceCapabilitiesKHR')
    my_bundle.surface_capabilites = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice, surface)

    # Set color space format
    vkGetPhysicalDeviceSurfaceFormatsKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceFormatsKHR')
    color_formats = vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface)

    for format in color_formats:
        if (format.format == VK_FORMAT_B8G8R8A8_UNORM and format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
            my_bundle.color_format =  format
        else:
            my_bundle.color_format =  color_formats[0]

    # Set present mode
    vkGetPhysicalDeviceSurfacePresentModesKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfacePresentModesKHR')
    present_modes = vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice, surface)

    for mode in present_modes:
        if mode == VK_PRESENT_MODE_MAILBOX_KHR:
            my_bundle.present_mode = mode
        else:
            my_bundle.present_mode = VK_PRESENT_MODE_FIFO_KHR

    # Set extent
    extent = VkExtent2D(width, height)
    extent.width = min(my_bundle.surface_capabilites.maxImageExtent.width, max(my_bundle.surface_capabilites.minImageExtent.width, extent.width))
    extent.height = min(my_bundle.surface_capabilites.maxImageExtent.height,max(my_bundle.surface_capabilites.minImageExtent.height, extent.height))
    my_bundle.extent = extent

    # Additional info setup for swapchain creation. In our case, the families should be the same
    if (queue_indices.graphics_family != queue_indices.present_family):
        img_sharing_mode = VK_SHARING_MODE_CONCURRENT
        queue_family_index_count = 2
        pointer_queue_family_indices = [queue_indices.graphics_family, queue_indices.present_family]
    else:
        img_sharing_mode = VK_SHARING_MODE_EXCLUSIVE
        queue_family_index_count = 0 # Number of family queues that access swapchain's images. Only needs to be set if sharing mode is Concurrent.
        pointer_queue_family_indices = None

    # Info for swapchain creation
    createInfo = VkSwapchainCreateInfoKHR(
        surface = surface, minImageCount = my_bundle.surface_capabilites.minImageCount, imageFormat = my_bundle.color_format.format,
        imageColorSpace = my_bundle.color_format.colorSpace, imageExtent = my_bundle.extent, imageArrayLayers = 1,
        imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT, imageSharingMode = img_sharing_mode,
        queueFamilyIndexCount = queue_family_index_count, pQueueFamilyIndices = pointer_queue_family_indices,
        preTransform = my_bundle.surface_capabilites.currentTransform, compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
        presentMode = my_bundle.present_mode, clipped = VK_TRUE
    )

    # Create actual swapchain
    vkCreateSwapchainKHR = vkGetDeviceProcAddr(logicalDevice, 'vkCreateSwapchainKHR')
    my_bundle.swapchain = vkCreateSwapchainKHR(logicalDevice, createInfo, None)
    

    vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(logicalDevice, 'vkGetSwapchainImagesKHR')
    images = vkGetSwapchainImagesKHR(logicalDevice, my_bundle.swapchain)

    # Creating an Image View for each image in swapchain
    for image in images:

        # Setting up info to create Image View
        components = VkComponentMapping(r = VK_COMPONENT_SWIZZLE_IDENTITY, g = VK_COMPONENT_SWIZZLE_IDENTITY, b = VK_COMPONENT_SWIZZLE_IDENTITY, a = VK_COMPONENT_SWIZZLE_IDENTITY)
        subresourceRange = VkImageSubresourceRange(aspectMask = VK_IMAGE_ASPECT_COLOR_BIT, baseMipLevel = 0, levelCount = 1, baseArrayLayer = 0, layerCount = 1)
        create_info = VkImageViewCreateInfo(image = image, viewType = VK_IMAGE_VIEW_TYPE_2D, format = my_bundle.color_format.format, components = components, 
            subresourceRange = subresourceRange)

        # Set custom frame class
        swapchain_frame = SwapChainFrame()
        swapchain_frame.image = image
        swapchain_frame.image_view = vkCreateImageView(device = logicalDevice, pCreateInfo = create_info, pAllocator = None) # Image view defines part of the image to be rendered

        # Set frames, made up by the swapchain/drivers images and ImageViews
        my_bundle.frames.append(swapchain_frame)
    
    return my_bundle