# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import math
import numbers
from typing import TYPE_CHECKING, Any

import numpy as np
from PIL import Image

import paddle
from paddle._typing import unreached

from ...base.framework import Variable
from . import (
    functional_cv2 as F_cv2,
    functional_pil as F_pil,
    functional_tensor as F_t,
)

if TYPE_CHECKING:
    from typing import Literal, TypeGuard, TypeVar, Union

    import numpy.typing as npt
    from PIL.Image import Image as PILImage
    from typing_extensions import TypeAlias

    from paddle import Tensor
    from paddle._typing import DataLayoutImage, Size2, Size3, Size4

    _InterpolationPil: TypeAlias = Literal[
        "nearest", "bilinear", "bicubic", "lanczos", "hamming"
    ]
    _InterpolationCv2: TypeAlias = Literal[
        "nearest", "bilinear", "area", "bicubic", "lanczos"
    ]
    _PaddingMode: TypeAlias = Literal[
        "constant", "edge", "reflect", "symmetric"
    ]
    _ImageDataT = TypeVar("_ImageDataT", Tensor, PILImage, npt.NDArray[Any])
    _ImageDataType = Union[Tensor, PILImage, npt.NDArray[Any]]

__all__ = []


def _is_pil_image(img: _ImageDataType) -> TypeGuard[PILImage]:
    return isinstance(img, Image.Image)


def _is_tensor_image(img: _ImageDataType) -> TypeGuard[Tensor]:
    """
    Return True if img is a Tensor for dynamic mode or Variable for static graph mode.
    """
    return isinstance(img, (paddle.Tensor, Variable))


def _is_numpy_image(img: _ImageDataType) -> TypeGuard[npt.NDArray[Any]]:
    return isinstance(img, np.ndarray) and (img.ndim in {2, 3})


def to_tensor(
    pic: PILImage | npt.NDArray[Any], data_format: DataLayoutImage = 'CHW'
) -> Tensor:
    """Converts a ``PIL.Image`` or ``numpy.ndarray`` to paddle.Tensor.

    Converts a PIL.Image or numpy.ndarray (H x W x C) to a paddle.Tensor of shape (C x H x W).

    If input is a grayscale image (H x W), it will be converted to an image of shape (H x W x 1).
    And the shape of output tensor will be (1 x H x W).

    If you want to keep the shape of output tensor as (H x W x C), you can set data_format = ``HWC`` .

    Converts a PIL.Image or numpy.ndarray in the range [0, 255] to a paddle.Tensor in the
    range [0.0, 1.0] if the PIL Image belongs to one of the modes (L, LA, P, I, F, RGB, YCbCr,
    RGBA, CMYK, 1) or if the numpy.ndarray has dtype = np.uint8.

    In the other cases, tensors are returned without scaling.

    Args:
        pic (PIL.Image|np.ndarray): Image to be converted to tensor.
        data_format (str, optional): Data format of output tensor, should be 'HWC' or
            'CHW'. Default: 'CHW'.

    Returns:
        Tensor: Converted image. Data type is same as input img.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> tensor = F.to_tensor(fake_img)
            >>> print(tensor.shape)
            [3, 256, 300]

    """
    if not (
        _is_pil_image(pic) or _is_numpy_image(pic) or _is_tensor_image(pic)
    ):
        raise TypeError(
            f'pic should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(pic)}'
        )

    if _is_pil_image(pic):
        return F_pil.to_tensor(pic, data_format)
    elif _is_numpy_image(pic):
        return F_cv2.to_tensor(pic, data_format)
    else:
        return pic if data_format.lower() == 'chw' else pic.transpose((1, 2, 0))


def resize(
    img: _ImageDataT,
    size: Size2,
    interpolation: _InterpolationPil | _InterpolationCv2 = 'bilinear',
) -> _ImageDataT:
    """
    Resizes the image to given size

    Args:
        input (PIL.Image|np.ndarray|paddle.Tensor): Image to be resized.
        size (int|list|tuple): Target size of input data, with (height, width) shape.
        interpolation (int|str, optional): Interpolation method. when use pil backend,
            support method are as following:
            - "nearest": Image.NEAREST,
            - "bilinear": Image.BILINEAR,
            - "bicubic": Image.BICUBIC,
            - "box": Image.BOX,
            - "lanczos": Image.LANCZOS,
            - "hamming": Image.HAMMING
            when use cv2 backend, support method are as following:
            - "nearest": cv2.INTER_NEAREST,
            - "bilinear": cv2.INTER_LINEAR,
            - "area": cv2.INTER_AREA,
            - "bicubic": cv2.INTER_CUBIC,
            - "lanczos": cv2.INTER_LANCZOS4

    Returns:
        PIL.Image|np.array|paddle.Tensor: Resized image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> converted_img = F.resize(fake_img, 224)
            >>> print(converted_img.size)
            (262, 224)

            >>> converted_img = F.resize(fake_img, (200, 150))
            >>> print(converted_img.size)
            (150, 200)
    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.resize(img, size, interpolation)
    elif _is_tensor_image(img):
        return F_t.resize(img, size, interpolation)
    else:
        return F_cv2.resize(img, size, interpolation)


def pad(
    img: _ImageDataT,
    padding: Size2 | Size4,
    fill: Size3 = 0,
    padding_mode: _PaddingMode = 'constant',
) -> _ImageDataT:
    """
    Pads the given PIL.Image or numpy.array or paddle.Tensor on all sides with specified padding mode and fill value.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be padded.
        padding (int|list|tuple): Padding on each border. If a single int is provided this
            is used to pad all borders. If list/tuple of length 2 is provided this is the padding
            on left/right and top/bottom respectively. If a list/tuple of length 4 is provided
            this is the padding for the left, top, right and bottom borders
            respectively.
        fill (float, optional): Pixel fill value for constant fill. If a tuple of
            length 3, it is used to fill R, G, B channels respectively.
            This value is only used when the padding_mode is constant. Default: 0.
        padding_mode: Type of padding. Should be: constant, edge, reflect or symmetric. Default: 'constant'.

            - constant: pads with a constant value, this value is specified with fill

            - edge: pads with the last value on the edge of the image

            - reflect: pads with reflection of image (without repeating the last value on the edge)

                       padding [1, 2, 3, 4] with 2 elements on both sides in reflect mode
                       will result in [3, 2, 1, 2, 3, 4, 3, 2]

            - symmetric: pads with reflection of image (repeating the last value on the edge)

                         padding [1, 2, 3, 4] with 2 elements on both sides in symmetric mode
                         will result in [2, 1, 1, 2, 3, 4, 4, 3]

    Returns:
        PIL.Image|np.array|paddle.Tensor: Padded image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> padded_img = F.pad(fake_img, padding=1)
            >>> print(padded_img.size)
            (302, 258)

            >>> padded_img = F.pad(fake_img, padding=(2, 1))
            >>> print(padded_img.size)
            (304, 258)
    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.pad(img, padding, fill, padding_mode)
    elif _is_tensor_image(img):
        return F_t.pad(img, padding, fill, padding_mode)
    else:
        return F_cv2.pad(img, padding, fill, padding_mode)


def crop(
    img: _ImageDataT, top: int, left: int, height: int, width: int
) -> _ImageDataT:
    """Crops the given Image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be cropped. (0,0) denotes the top left
            corner of the image.
        top (int): Vertical component of the top left corner of the crop box.
        left (int): Horizontal component of the top left corner of the crop box.
        height (int): Height of the crop box.
        width (int): Width of the crop box.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Cropped image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> cropped_img = F.crop(fake_img, 56, 150, 200, 100)
            >>> print(cropped_img.size)
            (100, 200)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.crop(img, top, left, height, width)
    elif _is_tensor_image(img):
        return F_t.crop(img, top, left, height, width)
    else:
        return F_cv2.crop(img, top, left, height, width)


def center_crop(img: _ImageDataT, output_size: Size2) -> _ImageDataT:
    """Crops the given Image and resize it to desired size.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be cropped. (0,0) denotes the top left corner of the image.
        output_size (sequence or int): (height, width) of the crop box. If int,
            it is used for both directions

    Returns:
        PIL.Image|np.array|paddle.Tensor: Cropped image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> cropped_img = F.center_crop(fake_img, (150, 100))
            >>> print(cropped_img.size)
            (100, 150)
    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.center_crop(img, output_size)
    elif _is_tensor_image(img):
        return F_t.center_crop(img, output_size)
    else:
        return F_cv2.center_crop(img, output_size)


def hflip(img: _ImageDataT) -> _ImageDataT:
    """Horizontally flips the given Image or np.array or paddle.Tensor.

    Args:
        img (PIL.Image|np.array|Tensor): Image to be flipped.

    Returns:
        PIL.Image|np.array|paddle.Tensor:  Horizontally flipped image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> flipped_img = F.hflip(fake_img)
            >>> print(flipped_img.size)
            (300, 256)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.hflip(img)
    elif _is_tensor_image(img):
        return F_t.hflip(img)
    else:
        return F_cv2.hflip(img)


def vflip(img: _ImageDataT) -> _ImageDataT:
    """Vertically flips the given Image or np.array or paddle.Tensor.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be flipped.

    Returns:
        PIL.Image|np.array|paddle.Tensor:  Vertically flipped image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> flipped_img = F.vflip(fake_img)
            >>> print(flipped_img.size)
            (300, 256)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.vflip(img)
    elif _is_tensor_image(img):
        return F_t.vflip(img)
    else:
        return F_cv2.vflip(img)


def adjust_brightness(
    img: _ImageDataT, brightness_factor: float
) -> _ImageDataT:
    """Adjusts brightness of an Image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be adjusted.
        brightness_factor (float): How much to adjust the brightness. Can be
            any non negative number. 0 gives a black image, 1 gives the
            original image while 2 increases the brightness by a factor of 2.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Brightness adjusted image.

    Examples:
        .. code-block:: python
            :name: code-example1

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> np.random.seed(2023)
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> print(fake_img.size)
            (300, 256)
            >>> print(fake_img.load()[1,1])
            (61, 155, 171)
            >>> converted_img = F.adjust_brightness(fake_img, 0.5)
            >>> print(converted_img.size)
            (300, 256)
            >>> print(converted_img.load()[1,1])
            (30, 77, 85)





    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.adjust_brightness(img, brightness_factor)
    elif _is_numpy_image(img):
        return F_cv2.adjust_brightness(img.astype(np.uint8), brightness_factor)
    else:
        return F_t.adjust_brightness(img, brightness_factor)


def adjust_contrast(img: _ImageDataT, contrast_factor: float) -> _ImageDataT:
    """Adjusts contrast of an Image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be adjusted.
        contrast_factor (float): How much to adjust the contrast. Can be any
            non negative number. 0 gives a solid gray image, 1 gives the
            original image while 2 increases the contrast by a factor of 2.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Contrast adjusted image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> converted_img = F.adjust_contrast(fake_img, 0.4)
            >>> print(converted_img.size)
            (300, 256)
    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.adjust_contrast(img, contrast_factor)
    elif _is_numpy_image(img):
        return F_cv2.adjust_contrast(img, contrast_factor)
    else:
        return F_t.adjust_contrast(img, contrast_factor)


def adjust_saturation(
    img: _ImageDataT, saturation_factor: float
) -> _ImageDataT:
    """Adjusts color saturation of an image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be adjusted.
        saturation_factor (float):  How much to adjust the saturation. 0 will
            give a black and white image, 1 will give the original image while
            2 will enhance the saturation by a factor of 2.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Saturation adjusted image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> converted_img = F.adjust_saturation(fake_img, 0.4)
            >>> print(converted_img.size)
            (300, 256)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.adjust_saturation(img, saturation_factor)
    elif _is_numpy_image(img):
        return F_cv2.adjust_saturation(img, saturation_factor)
    else:
        return F_t.adjust_saturation(img, saturation_factor)


def adjust_hue(img: _ImageDataT, hue_factor: float) -> _ImageDataT:
    """Adjusts hue of an image.

    The image hue is adjusted by converting the image to HSV and
    cyclically shifting the intensities in the hue channel (H).
    The image is then converted back to original image mode.

    `hue_factor` is the amount of shift in H channel and must be in the
    interval `[-0.5, 0.5]`.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be adjusted.
        hue_factor (float):  How much to shift the hue channel. Should be in
            [-0.5, 0.5]. 0.5 and -0.5 give complete reversal of hue channel in
            HSV space in positive and negative direction respectively.
            0 means no shift. Therefore, both -0.5 and 0.5 will give an image
            with complementary colors while 0 gives the original image.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Hue adjusted image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> converted_img = F.adjust_hue(fake_img, 0.4)
            >>> print(converted_img.size)
            (300, 256)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.adjust_hue(img, hue_factor)
    elif _is_numpy_image(img):
        return F_cv2.adjust_hue(img, hue_factor)
    else:
        return F_t.adjust_hue(img, hue_factor)


def _get_affine_matrix(center, angle, translate, scale, shear):
    # Affine matrix is : M = T * C * RotateScaleShear * C^-1
    # Ihe inverse one is : M^-1 = C * RotateScaleShear^-1 * C^-1 * T^-1
    rot = math.radians(angle)
    sx = math.radians(shear[0])
    sy = math.radians(shear[1])

    # Rotate and Shear without scaling
    a = math.cos(rot - sy) / math.cos(sy)
    b = -math.cos(rot - sy) * math.tan(sx) / math.cos(sy) - math.sin(rot)
    c = math.sin(rot - sy) / math.cos(sy)
    d = -math.sin(rot - sy) * math.tan(sx) / math.cos(sy) + math.cos(rot)

    # Center Translation
    cx, cy = center
    tx, ty = translate

    # Inverted rotation matrix with scale and shear
    # det([[a, b], [c, d]]) == 1, since det(rotation) = 1 and det(shear) = 1
    matrix = [d, -b, 0.0, -c, a, 0.0]
    matrix = [x / scale for x in matrix]
    # Apply inverse of translation and of center translation: RSS^-1 * C^-1 * T^-1
    matrix[2] += matrix[0] * (-cx - tx) + matrix[1] * (-cy - ty)
    matrix[5] += matrix[3] * (-cx - tx) + matrix[4] * (-cy - ty)
    # Apply center translation: C * RSS^-1 * C^-1 * T^-1
    matrix[2] += cx
    matrix[5] += cy

    return matrix


def affine(
    img: _ImageDataT,
    angle: float,
    translate: list[float] | tuple[float, float],
    scale: float,
    shear: list[float] | tuple[float, float],
    interpolation: _InterpolationPil | _InterpolationCv2 = "nearest",
    fill: Size3 = 0,
    center: list[float] | tuple[float, float] | None = None,
) -> _ImageDataT:
    """Apply affine transformation on the image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be affined.
        angle (int|float): The angle of the random rotation in clockwise order.
        translate (list[float]): Maximum absolute fraction for horizontal and vertical translations.
        scale (float): Scale factor for the image, scale should be positive.
        shear (list[float]): Shear angle values which are parallel to the x-axis and y-axis in clockwise order.
        interpolation (str, optional): Interpolation method. If omitted, or if the
            image has only one channel, it is set to PIL.Image.NEAREST or cv2.INTER_NEAREST
            according the backend.
            When use pil backend, support method are as following:
            - "nearest": Image.NEAREST,
            - "bilinear": Image.BILINEAR,
            - "bicubic": Image.BICUBIC
            When use cv2 backend, support method are as following:
            - "nearest": cv2.INTER_NEAREST,
            - "bilinear": cv2.INTER_LINEAR,
            - "bicubic": cv2.INTER_CUBIC
        fill (int|list|tuple, optional): Pixel fill value for the area outside the transformed
            image. If given a number, the value is used for all bands respectively.
        center (tuple|None, optional): Optional center of rotation, (x, y).
            Origin is the upper left corner.
            Default is the center of the image.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Affine Transformed image.

    Examples:
        .. code-block:: python

            >>> import paddle
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = paddle.randn((3, 256, 300)).astype(paddle.float32)
            >>> affined_img = F.affine(fake_img, 45, translate=[0.2, 0.2], scale=0.5, shear=[-10, 10])
            >>> print(affined_img.shape)
            [3, 256, 300]
    """

    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if not isinstance(angle, (int, float)):
        raise TypeError("Argument angle should be int or float")

    if not isinstance(translate, (list, tuple)):
        raise TypeError("Argument translate should be a sequence")

    if len(translate) != 2:
        raise ValueError("Argument translate should be a sequence of length 2")

    if scale <= 0.0:
        raise ValueError("Argument scale should be positive")

    if not isinstance(shear, (numbers.Number, (list, tuple))):
        raise TypeError(
            "Shear should be either a single value or a sequence of two values"
        )

    if not isinstance(interpolation, str):
        raise TypeError("Argument interpolation should be a string")

    if isinstance(angle, int):
        angle = float(angle)

    if isinstance(translate, tuple):
        translate = list(translate)

    if isinstance(shear, numbers.Number):
        shear = [shear, 0.0]

    if isinstance(shear, tuple):
        shear = list(shear)

    if len(shear) == 1:
        shear = [shear[0], shear[0]]

    if len(shear) != 2:
        raise ValueError(
            f"Shear should be a sequence containing two values. Got {shear}"
        )

    if center is not None and not isinstance(center, (list, tuple)):
        raise TypeError("Argument center should be a sequence")

    if _is_pil_image(img):
        width, height = img.size
        # center = (width * 0.5 + 0.5, height * 0.5 + 0.5)
        # it is visually better to estimate the center without 0.5 offset
        # otherwise image rotated by 90 degrees is shifted vs output image of F_t.affine
        if center is None:
            center = [width * 0.5, height * 0.5]
        matrix = _get_affine_matrix(center, angle, translate, scale, shear)
        return F_pil.affine(img, matrix, interpolation, fill)

    if _is_numpy_image(img):
        # get affine_matrix in F_cv2.affine() using cv2's functions
        width, height = img.shape[0:2]
        # center = (width * 0.5 + 0.5, height * 0.5 + 0.5)
        # it is visually better to estimate the center without 0.5 offset
        # otherwise image rotated by 90 degrees is shifted vs output image of F_t.affine
        if center is None:
            center = (width * 0.5, height * 0.5)
        return F_cv2.affine(
            img, angle, translate, scale, shear, interpolation, fill, center
        )

    if _is_tensor_image(img):
        center_f = [0.0, 0.0]
        if center is not None:
            height, width = img.shape[-1], img.shape[-2]
            # Center values should be in pixel coordinates but translated such that (0, 0) corresponds to image center.
            center_f = [
                1.0 * (c - s * 0.5) for c, s in zip(center, [width, height])
            ]
        translate_f = [1.0 * t for t in translate]
        matrix = _get_affine_matrix(center_f, angle, translate_f, scale, shear)
        return F_t.affine(img, matrix, interpolation, fill)

    unreached()


def rotate(
    img: _ImageDataT,
    angle: float,
    interpolation: _InterpolationPil | _InterpolationCv2 = "nearest",
    expand: bool = False,
    center: list[float] | tuple[float, float] | None = None,
    fill: Size3 = 0,
) -> _ImageDataT:
    """Rotates the image by angle.


    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be rotated.
        angle (float or int): In degrees degrees counter clockwise order.
        interpolation (str, optional): Interpolation method. If omitted, or if the
            image has only one channel, it is set to PIL.Image.NEAREST or cv2.INTER_NEAREST
            according the backend. when use pil backend, support method are as following:
            - "nearest": Image.NEAREST,
            - "bilinear": Image.BILINEAR,
            - "bicubic": Image.BICUBIC
            when use cv2 backend, support method are as following:
            - "nearest": cv2.INTER_NEAREST,
            - "bilinear": cv2.INTER_LINEAR,
            - "bicubic": cv2.INTER_CUBIC
        expand (bool, optional): Optional expansion flag.
            If true, expands the output image to make it large enough to hold the entire rotated image.
            If false or omitted, make the output image the same size as the input image.
            Note that the expand flag assumes rotation around the center and no translation.
        center (list|tuple|None, optional): Optional center of rotation.
            Origin is the upper left corner.
            Default is the center of the image.
        fill (list|tuple or int, optional): RGB pixel fill value for area outside the rotated image.
            If int, it is used for all channels respectively. Default value is 0.


    Returns:
        PIL.Image|np.array|paddle.Tensor: Rotated image.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> rotated_img = F.rotate(fake_img, 90)
            >>> print(rotated_img.size)
            (300, 256)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if isinstance(center, list):
        center = tuple(center)
    if isinstance(fill, list):
        fill = tuple(fill)

    if _is_pil_image(img):
        return F_pil.rotate(img, angle, interpolation, expand, center, fill)
    elif _is_tensor_image(img):
        return F_t.rotate(img, angle, interpolation, expand, center, fill)
    else:
        return F_cv2.rotate(img, angle, interpolation, expand, center, fill)


def _get_perspective_coeffs(startpoints, endpoints):
    """
    get coefficients (a, b, c, d, e, f, g, h) of the perspective transforms.

    In Perspective Transform each pixel (x, y) in the original image gets transformed as,
     (x, y) -> ( (ax + by + c) / (gx + hy + 1), (dx + ey + f) / (gx + hy + 1) )

    Args:
        startpoints (list[list[int]]): [top-left, top-right, bottom-right, bottom-left] of the original image,
        endpoints (list[list[int]]): [top-left, top-right, bottom-right, bottom-left] of the transformed image.

    Returns:
        output (list): octuple (a, b, c, d, e, f, g, h) for transforming each pixel.
    """
    a_matrix = np.zeros((2 * len(startpoints), 8))

    for i, (p1, p2) in enumerate(zip(endpoints, startpoints)):
        a_matrix[2 * i, :] = [
            p1[0],
            p1[1],
            1,
            0,
            0,
            0,
            -p2[0] * p1[0],
            -p2[0] * p1[1],
        ]
        a_matrix[2 * i + 1, :] = [
            0,
            0,
            0,
            p1[0],
            p1[1],
            1,
            -p2[1] * p1[0],
            -p2[1] * p1[1],
        ]

    b_matrix = np.array(startpoints).reshape([8])
    res = np.linalg.lstsq(a_matrix, b_matrix)[0]

    output = list(res)
    return output


def perspective(
    img: _ImageDataT,
    startpoints: list[list[int]],
    endpoints: list[list[int]],
    interpolation: _InterpolationPil | _InterpolationCv2 = 'nearest',
    fill: Size3 = 0,
) -> _ImageDataT:
    """Perform perspective transform of the given image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be transformed.
        startpoints (list of list of ints): List containing four lists of two integers corresponding to four corners
            ``[top-left, top-right, bottom-right, bottom-left]`` of the original image.
        endpoints (list of list of ints): List containing four lists of two integers corresponding to four corners
            ``[top-left, top-right, bottom-right, bottom-left]`` of the transformed image.
        interpolation (str, optional): Interpolation method. If omitted, or if the
            image has only one channel, it is set to PIL.Image.NEAREST or cv2.INTER_NEAREST
            according the backend.
            When use pil backend, support method are as following:
            - "nearest": Image.NEAREST,
            - "bilinear": Image.BILINEAR,
            - "bicubic": Image.BICUBIC
            When use cv2 backend, support method are as following:
            - "nearest": cv2.INTER_NEAREST,
            - "bilinear": cv2.INTER_LINEAR,
            - "bicubic": cv2.INTER_CUBIC
        fill (int|list|tuple, optional): Pixel fill value for the area outside the transformed
            image. If given a number, the value is used for all bands respectively.

    Returns:
        PIL.Image|np.array|paddle.Tensor: transformed Image.

    Examples:
        .. code-block:: python

            >>> import paddle
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = paddle.randn((3, 256, 300)).astype(paddle.float32)
            >>> startpoints = [[0, 0], [33, 0], [33, 25], [0, 25]]
            >>> endpoints = [[3, 2], [32, 3], [30, 24], [2, 25]]
            >>> perspectived_img = F.perspective(fake_img, startpoints, endpoints)
            >>> print(perspectived_img.shape)
            [3, 256, 300]

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        coeffs = _get_perspective_coeffs(startpoints, endpoints)
        return F_pil.perspective(img, coeffs, interpolation, fill)
    elif _is_tensor_image(img):
        coeffs = _get_perspective_coeffs(startpoints, endpoints)
        return F_t.perspective(img, coeffs, interpolation, fill)
    else:
        return F_cv2.perspective(
            img, startpoints, endpoints, interpolation, fill
        )


def to_grayscale(img: _ImageDataT, num_output_channels: int = 1) -> _ImageDataT:
    """Converts image to grayscale version of image.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): Image to be converted to grayscale.
        num_output_channels (int, optional): The number of channels for the output
            image. Single channel. Default: 1.
    Returns:
        PIL.Image|np.array|paddle.Tensor: Grayscale version of the image.
            if num_output_channels = 1 : returned image is single channel

            if num_output_channels = 3 : returned image is 3 channel with r = g = b

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> gray_img = F.to_grayscale(fake_img)
            >>> print(gray_img.size)
            (300, 256)

    """
    if not (
        _is_pil_image(img) or _is_numpy_image(img) or _is_tensor_image(img)
    ):
        raise TypeError(
            f'img should be PIL Image or Tensor Image or ndarray with dim=[2 or 3]. Got {type(img)}'
        )

    if _is_pil_image(img):
        return F_pil.to_grayscale(img, num_output_channels)
    elif _is_tensor_image(img):
        return F_t.to_grayscale(img, num_output_channels)
    else:
        return F_cv2.to_grayscale(img, num_output_channels)


def normalize(
    img: _ImageDataT,
    mean: list[float] | tuple[float, float, float],
    std: list[float] | tuple[float, float, float],
    data_format: DataLayoutImage = 'CHW',
    to_rgb: bool = False,
) -> _ImageDataT:
    """Normalizes a tensor or image with mean and standard deviation.

    Args:
        img (PIL.Image|np.array|paddle.Tensor): input data to be normalized.
        mean (list|tuple): Sequence of means for each channel.
        std (list|tuple): Sequence of standard deviations for each channel.
        data_format (str|None, optional): Data format of input img, should be 'HWC' or
            'CHW'. Default: 'CHW'.
        to_rgb (bool, optional): Whether to convert to rgb. If input is tensor,
            this option will be ignored. Default: False.

    Returns:
        PIL.Image|np.array|paddle.Tensor: Normalized mage. Data format is same as input img.

    Examples:
        .. code-block:: python

            >>> import numpy as np
            >>> from PIL import Image
            >>> from paddle.vision.transforms import functional as F
            >>> fake_img = (np.random.rand(256, 300, 3) * 255.).astype('uint8')
            >>> fake_img = Image.fromarray(fake_img)
            >>> mean = [127.5, 127.5, 127.5]
            >>> std = [127.5, 127.5, 127.5]
            >>> normalized_img = F.normalize(fake_img, mean, std, data_format='HWC')
            >>> print(normalized_img.max(), normalized_img.min())
            0.99215686 -1.0

    """

    if _is_tensor_image(img):
        return F_t.normalize(img, mean, std, data_format)
    else:
        if _is_pil_image(img):
            img = np.array(img).astype(np.float32)

        return F_cv2.normalize(img, mean, std, data_format, to_rgb)


def erase(
    img: _ImageDataT,
    i: int,
    j: int,
    h: int,
    w: int,
    v: npt.NDArray[Any] | Tensor,
    inplace: bool = False,
) -> _ImageDataT:
    """Erase the pixels of selected area in input image with given value.

    Args:
        img (paddle.Tensor | np.array | PIL.Image): input Tensor image.
             For Tensor input, the shape should be (C, H, W). For np.array input,
             the shape should be (H, W, C).
        i (int): y coordinate of the top-left point of erased region.
        j (int): x coordinate of the top-left point of erased region.
        h (int): Height of the erased region.
        w (int): Width of the erased region.
        v (paddle.Tensor | np.array): value used to replace the pixels in erased region. It
            should be np.array when img is np.array or PIL.Image.
        inplace (bool, optional): Whether this transform is inplace. Default: False.

    Returns:
        paddle.Tensor | np.array | PIL.Image: Erased image. The type is same with input image.

    Examples:
        .. code-block:: python

            >>> import paddle
            >>> paddle.seed(2023)
            >>> fake_img = paddle.randn((3, 2, 4)).astype(paddle.float32)
            >>> print(fake_img)
            Tensor(shape=[3, 2, 4], dtype=float32, place=Place(cpu), stop_gradient=True,
            [[[ 0.06132207,  1.11349595,  0.41906244, -0.24858207],
              [-1.85169315, -1.50370061,  1.73954511,  0.13331604]],
            [[ 1.66359663, -0.55764782, -0.59911072, -0.57773495],
             [-1.03176904, -0.33741450, -0.29695082, -1.50258386]],
            [[ 0.67233968, -1.07747352,  0.80170447, -0.06695852],
             [-1.85003340, -0.23008066,  0.65083790,  0.75387722]]])

            >>> values = paddle.zeros((1,1,1), dtype=paddle.float32)
            >>> result = paddle.vision.transforms.erase(fake_img, 0, 1, 1, 2, values)
            >>> print(result)
            Tensor(shape=[3, 2, 4], dtype=float32, place=Place(cpu), stop_gradient=True,
            [[[ 0.06132207,  0.        ,  0.        , -0.24858207],
              [-1.85169315, -1.50370061,  1.73954511,  0.13331604]],
            [[ 1.66359663,  0.        ,  0.        , -0.57773495],
             [-1.03176904, -0.33741450, -0.29695082, -1.50258386]],
            [[ 0.67233968,  0.        ,  0.        , -0.06695852],
             [-1.85003340, -0.23008066,  0.65083790,  0.75387722]]])

    """
    if _is_tensor_image(img):
        return F_t.erase(img, i, j, h, w, v, inplace=inplace)
    elif _is_pil_image(img):
        return F_pil.erase(img, i, j, h, w, v, inplace=inplace)
    else:
        return F_cv2.erase(img, i, j, h, w, v, inplace=inplace)
