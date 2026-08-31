"""VeilKit 核心编排层：帧封装 + 载体读写的统一入口。

对外提供与 CLI 无关的库 API，可直接被其他 Python 程序集成::

    from veilkit import hide_bytes, reveal_bytes

    stego = hide_bytes(open("cat.png", "rb").read(), b"hello", password="p@ss")
    assert reveal_bytes(stego, password="p@ss") == b"hello"
"""

from __future__ import annotations

import os

from .bitstream import bits_required
from .carriers import BINARY_CARRIERS, text as text_carrier
from .crypto import frame_size, open_frame, seal
from .errors import CapacityError, CarrierError, VeilKitError

_EXTENSION_MAP = {
    ".png": "png",
    ".bmp": "bmp",
    ".wav": "wav",
}

SUPPORTED_BINARY_TYPES = tuple(BINARY_CARRIERS.keys())
SUPPORTED_TEXT_ENCODING = "utf-8"


def detect_type(filename: str) -> str:
    """根据文件扩展名推断载体类型。"""
    _, ext = os.path.splitext(filename.lower())
    if ext not in _EXTENSION_MAP:
        raise CarrierError(
            f"无法从扩展名 {ext or '(空)'} 识别载体类型，"
            f"支持: {', '.join(SUPPORTED_BINARY_TYPES)} 与文本模式；"
            "也可通过 --type 显式指定"
        )
    return _EXTENSION_MAP[ext]


def _load_binary(kind: str, carrier: bytes):
    module = BINARY_CARRIERS.get(kind) if isinstance(kind, str) else None
    if module is None:
        raise CarrierError(
            f"未知二进制载体类型: {kind!r}，支持 {', '.join(SUPPORTED_BINARY_TYPES)}"
        )
    return module.load(carrier)


def capacity_bits(kind: str, carrier: bytes) -> int:
    """返回二进制载体可承载的比特数。"""
    return _load_binary(kind, carrier).capacity_bits


def capacity_human(kind: str, carrier: bytes, encrypted: bool) -> dict:
    """返回供 CLI/库使用的容量信息（比特、字节、当前负载上限）。"""
    bits = capacity_bits(kind, carrier)
    overhead = frame_size(0, encrypted) * 8
    usable_payload_bits = max(bits - overhead, 0)
    return {
        "type": kind,
        "capacity_bits": bits,
        "capacity_bytes": bits // 8,
        "frame_overhead_bytes": frame_size(0, encrypted),
        "max_payload_bytes": usable_payload_bits // 8,
        "encrypted": encrypted,
    }


def hide_bytes(kind: str, carrier: bytes, payload: bytes,
               password: str | None = None) -> bytes:
    """把 payload（可加密）隐写进二进制载体，返回新的载体字节串。"""
    image = _load_binary(kind, carrier)
    frame = seal(payload, password)
    needed = bits_required(frame)
    if needed > image.capacity_bits:
        raise CapacityError(
            f"载体容量不足：需要 {needed} bit（{len(frame)} 字节），"
            f"载体仅可写 {image.capacity_bits} bit"
            f"（约 {image.capacity_bits // 8} 字节）"
        )
    image.embed(frame)
    return image.render()


def reveal_bytes(kind: str, carrier: bytes, password: str | None = None) -> bytes:
    """从二进制载体中提取并校验/解密隐写负载。"""
    image = _load_binary(kind, carrier)
    reader = image.extract_reader()
    try:
        return open_frame(reader, password)
    except EOFError as exc:
        raise VeilKitError("载体比特流在读取过程中耗尽，数据可能不完整") from exc


# ---------------------------------------------------------------------------
# 文本载体便捷 API
# ---------------------------------------------------------------------------

def hide_text(cover_text: str, payload: str | bytes,
              password: str | None = None, position: str = "end") -> str:
    """把文本/字节负载隐写进封面文本，返回带不可见内容的字符串。"""
    if isinstance(payload, str):
        payload = payload.encode(SUPPORTED_TEXT_ENCODING)
    frame = seal(payload, password)
    return text_carrier.hide(cover_text, frame, position=position)


def reveal_text(stego_text: str, password: str | None = None) -> bytes:
    """从文本中提取隐写负载（返回字节；文本负载请自行 decode）。"""
    frame = text_carrier.extract(stego_text)
    return open_frame(_BytesReader(frame), password)


class _BytesReader:
    """让 bytes 兼容 open_frame 所需的 read(n) 接口。"""

    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0

    def read(self, size: int) -> bytes:
        chunk = self._data[self._pos:self._pos + size]
        self._pos += len(chunk)
        return chunk
