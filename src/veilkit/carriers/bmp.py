"""BMP 载体：24-bit 未压缩 BMP 的 LSB 隐写。

直接在原始文件字节上修改像素区（BGR），文件头、调色板、行填充字节全部原样保留，
因此输出文件与输入文件结构完全一致，仅像素最低位发生变化。
支持自底向上（height>0，常见）与自顶向下（height<0）两种扫描顺序。
"""

from __future__ import annotations

import struct

from ..bitstream import BitReader, iter_bits
from ..errors import CarrierError


class BMPImage:
    kind = "bmp"

    def __init__(self, data: bytes, pixel_offset: int, width: int,
                 abs_height: int, stride: int, top_down: bool):
        self._buf = bytearray(data)
        self.pixel_offset = pixel_offset
        self.width = width
        self.abs_height = abs_height
        self.stride = stride
        self.top_down = top_down

    @property
    def capacity_bits(self) -> int:
        return self.width * self.abs_height * 3

    def _iter_positions(self):
        row_bytes = self.width * 3
        for row in range(self.abs_height):
            row_start = self.pixel_offset + row * self.stride
            for offset in range(row_bytes):  # 行尾 4 字节对齐填充不可写
                yield row_start + offset

    def embed(self, frame: bytes) -> None:
        positions = self._iter_positions()
        written = 0
        for bit in iter_bits(frame):
            index = next(positions)
            self._buf[index] = (self._buf[index] & 0xFE) | bit
            written += 1
        if written != len(frame) * 8:
            raise CarrierError("内部错误：BMP 容量预检通过但写入未完成")

    def extract_reader(self) -> BitReader:
        positions = self._iter_positions()

        def next_bit():
            try:
                return self._buf[next(positions)] & 1
            except StopIteration:
                return None

        return BitReader(next_bit)

    def render(self) -> bytes:
        return bytes(self._buf)


def load(data: bytes) -> BMPImage:
    if data[:2] != b"BM":
        raise CarrierError("不是合法的 BMP 文件（缺少 BM 签名）")
    if len(data) < 14 + 40:
        raise CarrierError("BMP 文件过小或头部损坏")
    (pixel_offset,) = struct.unpack_from("<I", data, 10)
    (header_size,) = struct.unpack_from("<I", data, 14)
    if header_size != 40:
        raise CarrierError(
            f"仅支持 BITMAPINFOHEADER（头长 40），当前头长 {header_size}"
        )
    width, signed_height = struct.unpack_from("<ii", data, 18)
    planes, bpp = struct.unpack_from("<HH", data, 26)
    (compression,) = struct.unpack_from("<I", data, 30)
    if planes != 1:
        raise CarrierError(f"不支持的 BMP 色彩平面数: {planes}")
    if bpp != 24:
        raise CarrierError(f"仅支持 24-bit BMP，当前为 {bpp}-bit")
    if compression != 0:
        raise CarrierError("仅支持未压缩 BMP（BI_RGB），当前文件使用了压缩")
    if width <= 0 or signed_height == 0:
        raise CarrierError("BMP 宽高字段异常")
    top_down = signed_height < 0
    abs_height = abs(signed_height)
    stride = ((width * 3 + 3) // 4) * 4
    expected_end = pixel_offset + stride * abs_height
    if expected_end > len(data):
        raise CarrierError("BMP 像素区超出文件长度，文件可能已损坏")
    return BMPImage(data, pixel_offset, width, abs_height, stride, top_down)
