from config import *

class QueueFamilyIndices:

    def __init__(self):
        self.graphics_family = None
        self.present_family = None
    
    def is_complete(self):
        return (self.graphics_family != None and self.present_family != None)

    def get_unique_indices(self):

        unique_indices = [self.graphics_family,]
        if self.graphics_family != self.present_family:
            unique_indices.append(self.present_family)
        
        return unique_indices
    
def find_queue_families(device, instance, surface):
        
    indices = QueueFamilyIndices()

    # Get all queues
    queueFamilies = vkGetPhysicalDeviceQueueFamilyProperties(device)

    # Store first graphics and or present queue found
    for i,queueFamily in enumerate(queueFamilies):

        if queueFamily.queueFlags & VK_QUEUE_GRAPHICS_BIT:
            indices.graphics_family = i
        
        # To determine whether a queue family of a physical device supports presentation to a given surface. From khronos docs.
        surfaceSupport = vkGetInstanceProcAddr(instance, "vkGetPhysicalDeviceSurfaceSupportKHR")
        if surfaceSupport(device, i, surface):
            indices.present_family = i

        if indices.is_complete():
            break

    return indices