"""比特流工具：在字节串与 MSB-first 比特序列之间转换。

LSB 隐写按"每个可写字节承载 1 个比特"工作，因此需要把二进制帧展开成比特流写入，
提取时再把逐比特读到的内容重新拼回字节。统一采用高位优先（MSB-first）顺序。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator


def iter_bits(data: bytes) -> Iterator[int]:
    """按高位优先逐位产出字节串中的比特。"""
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


class BitReader:
    """从 ``next_bit()`` 回调中逐位取数并按字节还原。"""

    def __init__(self, next_bit: Callable[[], int]):
        self._next_bit = next_bit

    def read(self, size: int) -> bytes:
        if size <= 0:
            return b""
        out = bytearray(size)
        for i in range(size):
            value = 0
            for _ in range(8):
                bit = self._next_bit()
                if bit is None:
                    raise EOFError("载体比特流已耗尽")
                value = (value << 1) | (bit & 1)
            out[i] = value
        return bytes(out)


def bits_required(frame: bytes) -> int:
    return len(frame) * 8
