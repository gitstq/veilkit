"""载体实现注册表。"""

from . import bmp, png, text, wav

BINARY_CARRIERS = {
    "png": png,
    "bmp": bmp,
    "wav": wav,
}

__all__ = ["BINARY_CARRIERS", "bmp", "png", "text", "wav"]
