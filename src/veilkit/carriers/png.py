"""PNG 载体：纯标准库实现的 8-bit RGB/RGBA PNG 解码、重编码与 LSB 隐写。

不依赖 Pillow 等第三方图像库：
* 解码：解析 PNG 签名与 chunk，zlib 解压 IDAT，逆向全部 5 种行滤波器
  （None/Sub/Up/Average/Paeth），恢复逐行像素；
* 编码：统一以滤波器 0（None）重新写盘，输出的 PNG 完全符合规范，可被任意看图软件打开；
* 隐写：仅在 R/G/B 通道的最低有效位写入，alpha 通道保持不变，视觉上不可感知。

支持范围（超出时抛出清晰的 CarrierError）：位深 8bit、非隔行、色彩类型 2(RGB)/6(RGBA)。
"""

from __future__ import annotations

import struct
import zlib

from ..bitstream import BitReader, iter_bits
from ..errors import CarrierError

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_SUPPORTED_COLOR_TYPES = {2: 3, 6: 4}  # color type -> channels


def _paeth(a: int, b: int, c: int) -> int:
    predictor = a + b - c
    pa = abs(predictor - a)
    pb = abs(predictor - b)
    pc = abs(predictor - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw: bytes, width: int, height: int, channels: int) -> bytearray:
    stride = width * channels
    pixels = bytearray(stride * height)
    pos = 0
    prev_row = bytes(stride)
    for row_index in range(height):
        filter_type = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if len(line) < stride:
            raise CarrierError("PNG 图像数据不完整（IDAT 解压后长度异常）")
        bpp = channels  # 8-bit 下每像素字节数即通道数
        if filter_type == 0:
            pass
        elif filter_type == 1:  # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                line[i] = (line[i] + prev_row[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev_row[i]) >> 1)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upper_left = prev_row[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev_row[i], upper_left)) & 0xFF
        else:
            raise CarrierError(f"PNG 使用了不支持的行滤波器类型: {filter_type}")
        pixels[row_index * stride:(row_index + 1) * stride] = line
        prev_row = bytes(line)
    return pixels


def _iter_chunks(data: bytes):
    pos = len(_PNG_SIGNATURE)
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        if len(chunk_data) < length:
            raise CarrierError("PNG chunk 被截断")
        pos += 12 + length  # length(4)+type(4)+data+crc(4)
        yield chunk_type, chunk_data
        if chunk_type == b"IEND":
            break


class PNGImage:
    """解码后的 PNG 图像，负责 LSB 写入/读取与重新编码。"""

    kind = "png"

    def __init__(self, width: int, height: int, channels: int, pixels: bytearray):
        self.width = width
        self.height = height
        self.channels = channels
        self.pixels = pixels

    # -- 位置迭代：RGB 三通道可写，RGBA 的 alpha 下标跳过 --
    def _iter_positions(self):
        channels = self.channels
        for index in range(len(self.pixels)):
            if channels == 4 and index % 4 == 3:
                continue
            yield index

    @property
    def capacity_bits(self) -> int:
        return self.width * self.height * 3

    def embed(self, frame: bytes) -> None:
        positions = self._iter_positions()
        written = 0
        for bit in iter_bits(frame):
            try:
                index = next(positions)
            except StopIteration:
                break
            self.pixels[index] = (self.pixels[index] & 0xFE) | bit
            written += 1
        if written != len(frame) * 8:
            raise CarrierError("内部错误：PNG 容量预检通过但写入未完成")

    def extract_reader(self) -> BitReader:
        positions = self._iter_positions()

        def next_bit():
            try:
                index = next(positions)
            except StopIteration:
                return None
            return self.pixels[index] & 1

        return BitReader(next_bit)

    @staticmethod
    def _chunk(chunk_type: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + chunk_type
            + payload
            + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
        )

    def render(self) -> bytes:
        color_type = 6 if self.channels == 4 else 2
        ihdr = struct.pack(
            ">IIBBBBB", self.width, self.height, 8, color_type, 0, 0, 0
        )
        stride = self.width * self.channels
        raw = bytearray()
        for row in range(self.height):
            raw.append(0)  # 滤波器类型 None
            start = row * stride
            raw.extend(self.pixels[start:start + stride])
        compressed = zlib.compress(bytes(raw), 9)
        return (
            _PNG_SIGNATURE
            + self._chunk(b"IHDR", ihdr)
            + self._chunk(b"IDAT", compressed)
            + self._chunk(b"IEND", b"")
        )


def load(data: bytes) -> PNGImage:
    if not data.startswith(_PNG_SIGNATURE):
        raise CarrierError("不是合法的 PNG 文件（签名校验失败）")
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    for chunk_type, chunk_data in _iter_chunks(data):
        if chunk_type == b"IHDR":
            (
                width, height, bit_depth, color_type,
                _compression, _filter, interlace,
            ) = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
    if width is None:
        raise CarrierError("PNG 缺少 IHDR 块")
    if color_type not in _SUPPORTED_COLOR_TYPES:
        raise CarrierError(
            f"仅支持 RGB/RGBA 色彩类型（2/6），当前为 {color_type}；"
            "请先将图像转换为 8-bit RGB 或 RGBA"
        )
    if bit_depth != 8:
        raise CarrierError(f"仅支持 8-bit 位深，当前为 {bit_depth}-bit")
    if interlace != 0:
        raise CarrierError("暂不支持 Adam7 隔行扫描 PNG，请另存为非隔行格式")
    channels = _SUPPORTED_COLOR_TYPES[color_type]
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise CarrierError(f"PNG 数据解压失败: {exc}") from exc
    pixels = _unfilter(raw, width, height, channels)
    return PNGImage(width, height, channels, pixels)
