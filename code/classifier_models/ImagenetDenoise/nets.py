# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from .adv_model import AdvImageNetModel
from .third_party.imagenet_utils import ImageNetModel
from .resnet_model import (
    resnet_group, resnet_bottleneck, resnet_backbone)
from .resnet_model import denoising
from .resnet_model import resnet_backbone_for_analysis, resnet_bottleneck_for_analysis


NUM_BLOCKS = {
    50: [3, 4, 6, 3],
    101: [3, 4, 23, 3],
    152: [3, 8, 36, 3]
}


class ResNetModel(ImageNetModel):
    def __init__(self, args):
        self.num_blocks = NUM_BLOCKS[args.depth]

    def get_logits(self, image):
        return resnet_backbone(image, self.num_blocks, resnet_group, resnet_bottleneck)


class ResNetModel_For_Analysis(ImageNetModel):
    def __init__(self, args):
        self.num_blocks = NUM_BLOCKS[args.depth]

    def get_logits(self, image):
        return resnet_backbone_for_analysis(image, self.num_blocks, resnet_group, resnet_bottleneck_for_analysis)

class ResNetDenoiseModel(ImageNetModel):
    def __init__(self, args):
        self.num_blocks = NUM_BLOCKS[args.depth]

    def get_logits(self, image):

        def group_func(name, *args):
            """
            Feature Denoising, Sec 6:
            we add 4 denoising blocks to a ResNet: each is added after the
            last residual block of res2, res3, res4, and res5, respectively.
            """
            l = resnet_group(name, *args)
            l = denoising(name + '_denoise', l, embed=True, softmax=True)
            return l

        return resnet_backbone(image, self.num_blocks, group_func, resnet_bottleneck)


class ResNeXtDenoiseAllModel(ImageNetModel):
    """
    ResNeXt 32x8d that performs denoising after every residual block.
    """
    def __init__(self, args):
        self.num_blocks = NUM_BLOCKS[args.depth]

    def get_logits(self, image):

        print(image.shape.as_list())
        def block_func(l, ch_out, stride):
            """
            Feature Denoising, Sec 6.2:
            The winning entry, shown in the blue bar, was based on our method by using
            a ResNeXt101-32×8 backbone
            with non-local denoising blocks added to all residual blocks.
            """
            l = resnet_bottleneck(l, ch_out, stride, group=32, res2_bottleneck=8)
            l = denoising('non_local', l, embed=False, softmax=False)
            return l

        return resnet_backbone(image, self.num_blocks, resnet_group, block_func)
