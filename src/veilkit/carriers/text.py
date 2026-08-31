"""文本载体：基于 Unicode 零宽字符的隐写。

把二进制帧逐比特映射为视觉不可见的零宽字符，嵌入任意可见"封面文本"中：

==============  ====================
比特/符号        Unicode 字符
==============  ====================
0               ZWSP  U+200B（零宽空格）
1               ZWNJ  U+200C（零宽非连接符）
字节分隔符       ZWJ   U+200D（零宽连接符）
块边界           WJ    U+2060（字词连接符）
==============  ====================

封面文本在支持 Unicode 的任何地方（聊天、代码注释、文档）看起来都与原文一致。
提取时优先识别成对块边界；缺失边界时回退为"扫描全部零宽字符"，提升鲁棒性。
"""

from __future__ import annotations

from ..errors import CarrierError

ZERO = "\u200B"
ONE = "\u200C"
BYTE_SEP = "\u200D"
BLOCK_MARK = "\u2060"

_INVISIBLE = {ZERO, ONE, BYTE_SEP, BLOCK_MARK}
_BIT_MAP = {ZERO: 0, ONE: 1}


def encode_block(payload: bytes) -> str:
    """把字节串编码为零宽字符块（含首尾块边界）。"""
    parts = [BLOCK_MARK]
    for byte in payload:
        for shift in range(7, -1, -1):
            parts.append(ZERO if ((byte >> shift) & 1) == 0 else ONE)
        parts.append(BYTE_SEP)
    parts.append(BLOCK_MARK)
    return "".join(parts)


def hide(cover_text: str, payload: bytes, position: str = "end") -> str:
    """把隐写块嵌入封面文本。

    position:
      * ``end``（默认）：追加到文末；
      * ``start``：置于文首；
      * ``split``：在第一个空白处分隔插入，无空白时退化为 end。
    """
    block = encode_block(payload)
    cover_text = cover_text or ""
    if position == "start":
        return block + cover_text
    if position == "split":
        words = cover_text.split(" ", 1)
        if len(words) == 2:
            return words[0] + " " + block + words[1]
    return cover_text + block


def _decode_symbols(symbols: list[str]) -> bytes:
    out = bytearray()
    current = 0
    bit_count = 0
    for symbol in symbols:
        if symbol == BYTE_SEP:
            if bit_count > 0:
                out.append(current)
                current, bit_count = 0, 0
            continue
        bit = _BIT_MAP.get(symbol)
        if bit is None:
            continue
        current = (current << 1) | bit
        bit_count += 1
        if bit_count == 8:
            out.append(current)
            current, bit_count = 0, 0
    return bytes(out)


def extract(text: str) -> bytes:
    """从文本中提取隐写字节帧；找不到任何零宽符号时抛 CarrierError。"""
    # 优先：成对块边界之间的内容
    first = text.find(BLOCK_MARK)
    if first != -1:
        second = text.find(BLOCK_MARK, first + 1)
        if second != -1:
            inner = [c for c in text[first + 1:second] if c in _INVISIBLE]
            if inner:
                return _decode_symbols(inner)
    # 回退：扫描全文零宽比特符
    symbols = [c for c in text if c in _BIT_MAP or c == BYTE_SEP]
    if not symbols:
        raise CarrierError("文本中未检测到零宽字符隐写内容")
    return _decode_symbols(symbols)


def strip(text: str) -> str:
    """移除文本中的全部隐写符号，恢复干净的封面文本。"""
    return "".join(c for c in text if c not in _INVISIBLE)
