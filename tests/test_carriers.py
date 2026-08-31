"""载体层测试：PNG/BMP/WAV/文本的编解码与端到端隐写往返。"""

import os
import struct
import unittest
import zlib

from veilkit import hide_bytes, reveal_bytes, hide_text, reveal_text
from veilkit.carriers import bmp as bmp_mod
from veilkit.carriers import png as png_mod
from veilkit.carriers import text as text_mod
from veilkit.carriers import wav as wav_mod
from veilkit.core import capacity_human
from veilkit.errors import CapacityError, CarrierError, NoHiddenDataError


def lcg_bytes(seed: int, count: int) -> bytes:
    """可复现的确定性伪随机字节，避免测试依赖 random 状态。"""
    out = bytearray(count)
    state = seed
    for i in range(count):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        out[i] = state & 0xFF
    return bytes(out)


# ---------------------------------------------------------------------------
# PNG
# ---------------------------------------------------------------------------

def make_png(width: int, height: int, channels: int = 3,
             filters: tuple[int, ...] | None = None) -> bytes:
    """用自身编码器（或指定混合滤波器）合成 PNG。"""
    pixels = lcg_bytes(7, width * height * channels)
    if filters is None:
        img = png_mod.PNGImage(width, height, channels, bytearray(pixels))
        return img.render()
    # 手工构造混合行滤波器，验证解码器对 5 种滤波器的逆向
    stride = width * channels
    raw = bytearray()
    prev = bytes(stride)
    for row in range(height):
        ftype = filters[row % len(filters)]
        line = pixels[row * stride:(row + 1) * stride]
        filtered = bytearray(stride)
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = prev[i]
            ul = prev[i - channels] if i >= channels else 0
            if ftype == 0:
                filtered[i] = line[i]
            elif ftype == 1:
                filtered[i] = (line[i] - left) & 0xFF
            elif ftype == 2:
                filtered[i] = (line[i] - up) & 0xFF
            elif ftype == 3:
                filtered[i] = (line[i] - ((left + up) >> 1)) & 0xFF
            else:
                p = left + up - ul
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - ul)
                pred = left if pa <= pb and pa <= pc else (up if pb <= pc else ul)
                filtered[i] = (line[i] - pred) & 0xFF
        raw.append(ftype)
        raw.extend(filtered)
        prev = line
    ihdr = struct.pack(">IIBBBBB", width, height, 8,
                       6 if channels == 4 else 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_mod.PNGImage._chunk(b"IHDR", ihdr)  # type: ignore[attr-defined]
        + png_mod.PNGImage._chunk(b"IDAT", zlib.compress(bytes(raw), 9))  # type: ignore[attr-defined]
        + png_mod.PNGImage._chunk(b"IEND", b"")  # type: ignore[attr-defined]
    )


class TestPNG(unittest.TestCase):
    def test_mixed_filters_decode(self):
        data = make_png(13, 5, 3, filters=(0, 1, 2, 3, 4))
        img = png_mod.load(data)
        expected = lcg_bytes(7, 13 * 5 * 3)
        self.assertEqual(bytes(img.pixels), expected)

    def test_rgba_roundtrip(self):
        carrier = make_png(24, 24, 4)
        stego = hide_bytes("png", carrier, b"rgba-secret", password="k")
        out = reveal_bytes("png", stego, password="k")
        self.assertEqual(out, b"rgba-secret")

    def test_alpha_channel_untouched(self):
        carrier = make_png(16, 16, 4)
        before = png_mod.load(carrier)
        alpha_before = bytes(before.pixels[3::4])
        stego = hide_bytes("png", carrier, b"x", None)
        after = png_mod.load(stego)
        self.assertEqual(bytes(after.pixels[3::4]), alpha_before)

    def test_bad_signature(self):
        with self.assertRaises(CarrierError):
            png_mod.load(b"not a png file at all" * 4)

    def test_capacity_report(self):
        carrier = make_png(32, 32, 3)
        info = capacity_human("png", carrier, encrypted=True)
        self.assertEqual(info["capacity_bits"], 32 * 32 * 3)
        self.assertGreater(info["max_payload_bytes"], 0)


# ---------------------------------------------------------------------------
# BMP
# ---------------------------------------------------------------------------

def make_bmp(width: int, height: int) -> bytes:
    stride = ((width * 3 + 3) // 4) * 4
    pixel_offset = 14 + 40
    filesize = pixel_offset + stride * height
    file_header = b"BM" + struct.pack("<IHHI", filesize, 0, 0, pixel_offset)
    info_header = struct.pack(
        "<IiiHHIIiiII", 40, width, height, 1, 24, 0,
        stride * height, 2835, 2835, 0, 0,
    )
    pixels = bytearray(lcg_bytes(13, width * height * 3))
    rows = bytearray()
    for row in range(height):  # 自底向上，附带行填充
        rows.extend(pixels[row * width * 3:(row + 1) * width * 3])
        rows.extend(b"\x00" * (stride - width * 3))
    return file_header + info_header + bytes(rows)


class TestBMP(unittest.TestCase):
    def test_roundtrip_encrypted(self):
        carrier = make_bmp(40, 40)
        stego = hide_bytes("bmp", carrier, b"bmp payload" * 3, password="pw")
        self.assertEqual(reveal_bytes("bmp", stego, "pw"), b"bmp payload" * 3)

    def test_header_bytes_preserved(self):
        carrier = make_bmp(17, 9)
        stego = hide_bytes("bmp", carrier, b"h", None)
        self.assertEqual(stego[:54], carrier[:54])

    def test_reject_non_24bit(self):
        bad = bytearray(make_bmp(8, 8))
        struct.pack_into("<H", bad, 28, 32)
        with self.assertRaises(CarrierError):
            bmp_mod.load(bytes(bad))


# ---------------------------------------------------------------------------
# WAV
# ---------------------------------------------------------------------------

def make_wav(channels: int, bits: int, sample_count: int) -> bytes:
    frame_size = channels * bits // 8
    data = lcg_bytes(21, sample_count * frame_size)
    fmt = struct.pack("<HHIIHH", 1, channels, 48000,
                      48000 * frame_size, frame_size, bits)
    riff_size = 4 + (8 + len(fmt)) + (8 + len(data))
    return (
        b"RIFF" + struct.pack("<I", riff_size) + b"WAVE"
        + b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(data)) + data
    )


class TestWAV(unittest.TestCase):
    def test_8bit_mono_roundtrip(self):
        carrier = make_wav(1, 8, 4000)
        stego = hide_bytes("wav", carrier, b"audio8", None)
        self.assertEqual(reveal_bytes("wav", stego), b"audio8")

    def test_16bit_stereo_roundtrip(self):
        carrier = make_wav(2, 16, 6000)
        stego = hide_bytes("wav", carrier, b"audio16" * 4, password="z")
        self.assertEqual(reveal_bytes("wav", stego, "z"), b"audio16" * 4)

    def test_reject_compressed(self):
        bad = bytearray(make_wav(1, 16, 1000))
        # audio_format 位于 fmt 负载起点（RIFF12 + "fmt "(4)+size(4) = 20）
        struct.pack_into("<H", bad, 20, 3)
        with self.assertRaises(CarrierError):
            wav_mod.load(bytes(bad))


# ---------------------------------------------------------------------------
# 文本零宽载体
# ---------------------------------------------------------------------------

class TestText(unittest.TestCase):
    def test_text_roundtrip_plain(self):
        stego = hide_text("这是一段正常的封面文本。", "你好，隐写世界")
        self.assertTrue(stego.startswith("这是一段正常的封面文本。"))
        self.assertEqual(reveal_text(stego).decode(), "你好，隐写世界")

    def test_text_roundtrip_encrypted(self):
        stego = hide_text("innocent cover text", b"binary\x00\x01payload", "pw")
        self.assertEqual(reveal_text(stego, "pw"), b"binary\x00\x01payload")

    def test_text_split_position(self):
        stego = hide_text("hello world", b"x", None, position="split")
        self.assertEqual(reveal_text(stego), b"x")
        self.assertEqual(text_mod.strip(stego), "hello world")

    def test_extract_without_mark_fallback(self):
        block = text_mod.encode_block(b"fb")
        stripped_marks = block.replace(text_mod.BLOCK_MARK, "")
        self.assertEqual(text_mod.extract(stripped_marks), b"fb")

    def test_empty_text_raises(self):
        with self.assertRaises(CarrierError):
            text_mod.extract("nothing hidden here")


# ---------------------------------------------------------------------------
# 通用：容量与异常
# ---------------------------------------------------------------------------

class TestCommon(unittest.TestCase):
    def test_capacity_overflow(self):
        small = make_png(2, 2, 3)  # 仅 12 bit
        with self.assertRaises(CapacityError):
            hide_bytes("png", small, b"too long payload", None)

    def test_clean_carrier_has_no_frame(self):
        clean = make_png(40, 40, 3)
        with self.assertRaises(NoHiddenDataError):
            reveal_bytes("png", clean)


if __name__ == "__main__":
    unittest.main()
