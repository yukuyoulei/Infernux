#pragma once

#include <vulkan/vulkan.h>

namespace infernux::vkrender
{

inline constexpr VkPipelineStageFlags kShaderUniformReadStages =
    VK_PIPELINE_STAGE_VERTEX_SHADER_BIT | VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;

inline VkSubpassDependency MakePipelineCompatibleSubpassDependency()
{
    VkSubpassDependency dependency{};
    dependency.srcSubpass = VK_SUBPASS_EXTERNAL;
    dependency.dstSubpass = 0;
    dependency.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |
                              VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT;
    dependency.srcAccessMask = VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    dependency.dstStageMask =
        VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT | VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT;
    dependency.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    return dependency;
}

inline VkDescriptorSetLayoutBinding MakeDescriptorSetLayoutBinding(uint32_t binding, VkDescriptorType descriptorType,
                                                                   VkShaderStageFlags stageFlags,
                                                                   uint32_t descriptorCount = 1)
{
    VkDescriptorSetLayoutBinding layoutBinding{};
    layoutBinding.binding = binding;
    layoutBinding.descriptorType = descriptorType;
    layoutBinding.descriptorCount = descriptorCount;
    layoutBinding.stageFlags = stageFlags;
    return layoutBinding;
}

inline bool CreateDescriptorSetLayout(VkDevice device, const VkDescriptorSetLayoutBinding *bindings,
                                      uint32_t bindingCount, VkDescriptorSetLayout &outLayout)
{
    VkDescriptorSetLayoutCreateInfo layoutInfo{};
    layoutInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    layoutInfo.bindingCount = bindingCount;
    layoutInfo.pBindings = bindingCount > 0 ? bindings : nullptr;

    outLayout = VK_NULL_HANDLE;
    return vkCreateDescriptorSetLayout(device, &layoutInfo, nullptr, &outLayout) == VK_SUCCESS;
}

inline bool AllocateDescriptorSet(VkDevice device, VkDescriptorPool descriptorPool, VkDescriptorSetLayout layout,
                                  VkDescriptorSet &outDescriptorSet)
{
    VkDescriptorSetAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    allocInfo.descriptorPool = descriptorPool;
    allocInfo.descriptorSetCount = 1;
    allocInfo.pSetLayouts = &layout;

    outDescriptorSet = VK_NULL_HANDLE;
    return vkAllocateDescriptorSets(device, &allocInfo, &outDescriptorSet) == VK_SUCCESS;
}

inline void UpdateDescriptorSetWithBuffer(VkDevice device, VkDescriptorSet descriptorSet, uint32_t binding,
                                          VkDescriptorType descriptorType, const VkDescriptorBufferInfo &bufferInfo,
                                          uint32_t descriptorCount = 1)
{
    VkWriteDescriptorSet write{};
    write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write.dstSet = descriptorSet;
    write.dstBinding = binding;
    write.dstArrayElement = 0;
    write.descriptorType = descriptorType;
    write.descriptorCount = descriptorCount;
    write.pBufferInfo = &bufferInfo;
    vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
}

inline void UpdateDescriptorSetWithImage(VkDevice device, VkDescriptorSet descriptorSet, uint32_t binding,
                                         const VkDescriptorImageInfo &imageInfo,
                                         VkDescriptorType descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
                                         uint32_t descriptorCount = 1)
{
    VkWriteDescriptorSet write{};
    write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write.dstSet = descriptorSet;
    write.dstBinding = binding;
    write.dstArrayElement = 0;
    write.descriptorType = descriptorType;
    write.descriptorCount = descriptorCount;
    write.pImageInfo = &imageInfo;
    vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
}

inline void CmdBarrierUniformReadToTransferWrite(VkCommandBuffer cmdBuf)
{
    VkMemoryBarrier barrier{};
    barrier.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    barrier.srcAccessMask = VK_ACCESS_UNIFORM_READ_BIT;
    barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    vkCmdPipelineBarrier(cmdBuf, kShaderUniformReadStages, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 1, &barrier, 0, nullptr,
                         0, nullptr);
}

inline void CmdBarrierTransferWriteToUniformRead(VkCommandBuffer cmdBuf)
{
    VkMemoryBarrier barrier{};
    barrier.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    barrier.dstAccessMask = VK_ACCESS_UNIFORM_READ_BIT;
    vkCmdPipelineBarrier(cmdBuf, VK_PIPELINE_STAGE_TRANSFER_BIT, kShaderUniformReadStages, 0, 1, &barrier, 0, nullptr,
                         0, nullptr);
}

} // namespace infernux::vkrender