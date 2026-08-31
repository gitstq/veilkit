"""WAV 载体：PCM 8/16-bit 单/立体声 WAV 的采样 LSB 隐写。

逐 chunk 解析 RIFF 容器，只改写 data 块中每个采样的最低位，其余字节（fmt、LIST、
fact 等附加块）原样保留，并在渲染时回填正确的块长度。8-bit PCM 为无符号整数、
16-bit PCM 为小端有符号整数，二者的最低位都落在采样的第 1 个可写比特上。
"""

from __future__ import annotations

import struct

from ..bitstream import BitReader, iter_bits
from ..errors import CarrierError


class WAVAudio:
    kind = "wav"

    def __init__(self, data: bytes, data_pos: int, data_len: int,
                 channels: int, bits_per_sample: int):
        self._buf = bytearray(data)
        self.data_pos = data_pos  # data chunk 负载起点（跳过 id+size）
        self.data_len = data_len
        self.channels = channels
        self.bits_per_sample = bits_per_sample
        self.sample_count = (data_len // (channels * bits_per_sample // 8)) * channels

    @property
    def capacity_bits(self) -> int:
        return self.sample_count

    def _iter_positions(self):
        if self.bits_per_sample == 8:
            step = 1
            offset = 0
        else:  # 16-bit：小端序，最低位在低字节
            step = 2
            offset = 0
        sample_stride = step * self.channels
        for frame_start in range(self.data_pos,
                                 self.data_pos + self.data_len - sample_stride + 1,
                                 sample_stride):
            for channel in range(self.channels):
                yield frame_start + channel * step + offset

    def embed(self, frame: bytes) -> None:
        positions = self._iter_positions()
        written = 0
        for bit in iter_bits(frame):
            index = next(positions)
            self._buf[index] = (self._buf[index] & 0xFE) | bit
            written += 1
        if written != len(frame) * 8:
            raise CarrierError("内部错误：WAV 容量预检通过但写入未完成")

    def extract_reader(self) -> BitReader:
        positions = self._iter_positions()

        def next_bit():
            try:
                return self._buf[next(positions)] & 1
            except StopIteration:
                return None

        return BitReader(next_bit)

    def render(self) -> bytes:
        # 长度未发生变化，回填 RIFF 总长度与 data 块长度以保证严谨性
        struct.pack_into("<I", self._buf, 4, len(self._buf) - 8)
        struct.pack_into("<I", self._buf, self.data_pos - 4, self.data_len)
        return bytes(self._buf)


def load(data: bytes) -> WAVAudio:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise CarrierError("不是合法的 WAV 文件（RIFF/WAVE 签名校验失败）")
    channels = bits_per_sample = None
    data_pos = data_len = None
    pos = 12
    while pos + 8 <= len(data):
        chunk_id = data[pos:pos + 4]
        (chunk_size,) = struct.unpack_from("<I", data, pos + 4)
        payload_pos = pos + 8
        if chunk_id == b"fmt ":
            if chunk_size < 16:
                raise CarrierError("WAV fmt 块长度异常")
            (audio_format,) = struct.unpack_from("<H", data, payload_pos)
            channels, _sample_rate, _byte_rate, _block_align, bits = \
                struct.unpack_from("<HHIIH", data, payload_pos + 2)
            bits_per_sample = bits
            if audio_format != 1:
                raise CarrierError(
                    f"仅支持未压缩 PCM WAV（format=1），当前 format={audio_format}"
                )
        elif chunk_id == b"data":
            data_pos, data_len = payload_pos, chunk_size
        pos = payload_pos + chunk_size + (chunk_size & 1)  # RIFF 块偶数字节对齐
    if channels is None or bits_per_sample is None:
        raise CarrierError("WAV 缺少 fmt 块")
    if data_pos is None:
        raise CarrierError("WAV 缺少 data 块")
    if bits_per_sample not in (8, 16):
        raise CarrierError(f"仅支持 8/16-bit PCM，当前为 {bits_per_sample}-bit")
    if data_pos + data_len > len(data):
        raise CarrierError("WAV data 块超出文件长度，文件可能已损坏")
    return WAVAudio(data, data_pos, data_len, channels, bits_per_sample)
