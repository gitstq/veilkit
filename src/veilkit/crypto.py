"""VeilKit 安全层：纯标准库实现的 ChaCha20 + PBKDF2 + HMAC 帧封装。

设计要点
--------
* 对称流密码采用 RFC 8439 定义的 ChaCha20（32 字节密钥、96-bit nonce、32-bit 计数器），
  实现可对照 RFC 2.4.2 节的公开测试向量，测试套件中包含 Known-Answer-Test。
* 密钥派生使用 PBKDF2-HMAC-SHA256（200_000 轮，16 字节随机盐），一次派生 64 字节，
  前 32 字节作为加密密钥、后 32 字节作为 MAC 密钥，做到密钥隔离。
* 采用 encrypt-then-MAC：HMAC-SHA256 覆盖帧头与密文，任何比特级篡改或口令错误
  都会在解密前被明确检出（常量时间比较）。
* 无口令模式仅做帧封装（不加密），适用于不要求保密性的演示/水印场景。

帧格式（大端序）::

    明文模式:  b"VEILKIT1" | flags(1)=0x00      | length(4) | payload
    加密模式:  b"VEILKIT1" | flags(1)=0x01      | salt(16) | nonce(12)
               | length(4) | ciphertext         | hmac_sha256(32)
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct

from .errors import AuthError, NoHiddenDataError, PasswordRequiredError

MAGIC = b"VEILKIT1"
_FLAG_ENCRYPTED = 0x01
_PBKDF2_ITERATIONS = 200_000
_SALT_LEN = 16
_NONCE_LEN = 12
_TAG_LEN = 32
_KEY_LEN = 32

# ---------------------------------------------------------------------------
# ChaCha20 (RFC 8439, 纯 Python 实现)
# ---------------------------------------------------------------------------

_MASK32 = 0xFFFFFFFF


def _rotl32(value: int, shift: int) -> int:
    return ((value << shift) & _MASK32) | (value >> (32 - shift))


def _quarter_round(state: list[int], a: int, b: int, c: int, d: int) -> None:
    state[a] = (state[a] + state[b]) & _MASK32
    state[d] = _rotl32(state[d] ^ state[a], 16)
    state[c] = (state[c] + state[d]) & _MASK32
    state[b] = _rotl32(state[b] ^ state[c], 12)
    state[a] = (state[a] + state[b]) & _MASK32
    state[d] = _rotl32(state[d] ^ state[a], 8)
    state[c] = (state[c] + state[d]) & _MASK32
    state[b] = _rotl32(state[b] ^ state[c], 7)


def chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    """生成单个 64 字节 ChaCha20 密钥流块。"""
    if len(key) != _KEY_LEN:
        raise ValueError("ChaCha20 key must be exactly 32 bytes")
    if len(nonce) != _NONCE_LEN:
        raise ValueError("ChaCha20 nonce must be exactly 12 bytes")
    state = [
        0x61707865, 0x3320646E, 0x79622D32, 0x6B206574,
        *struct.unpack("<8I", key),
        counter & _MASK32,
        *struct.unpack("<3I", nonce),
    ]
    working = list(state)
    for _ in range(10):  # 20 轮 = 10 次双轮
        _quarter_round(working, 0, 4, 8, 12)
        _quarter_round(working, 1, 5, 9, 13)
        _quarter_round(working, 2, 6, 10, 14)
        _quarter_round(working, 3, 7, 11, 15)
        _quarter_round(working, 0, 5, 10, 15)
        _quarter_round(working, 1, 6, 11, 12)
        _quarter_round(working, 2, 7, 8, 13)
        _quarter_round(working, 3, 4, 9, 14)
    return struct.pack("<16I", *((working[i] + state[i]) & _MASK32 for i in range(16)))


def chacha20_xor(key: bytes, nonce: bytes, data: bytes, counter: int = 0) -> bytes:
    """用 ChaCha20 密钥流对 data 做异或（加解密同构）。"""
    out = bytearray(len(data))
    block_index = 0
    while block_index * 64 < len(data):
        stream = chacha20_block(key, (counter + block_index) & _MASK32, nonce)
        start = block_index * 64
        for i, byte in enumerate(data[start:start + 64]):
            out[start + i] = byte ^ stream[i]
        block_index += 1
    return bytes(out)


# ---------------------------------------------------------------------------
# 密钥派生与帧封装
# ---------------------------------------------------------------------------

def _derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    material = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, dklen=64
    )
    return material[:_KEY_LEN], material[_KEY_LEN:]


def seal(payload: bytes, password: str | None) -> bytes:
    """把明文负载封装为可写入载体的二进制帧。"""
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload must be bytes")
    if password is None:
        return MAGIC + bytes([0]) + struct.pack(">I", len(payload)) + bytes(payload)

    salt = os.urandom(_SALT_LEN)
    nonce = os.urandom(_NONCE_LEN)
    enc_key, mac_key = _derive_keys(password, salt)
    ciphertext = chacha20_xor(enc_key, nonce, bytes(payload))
    body = (
        MAGIC
        + bytes([_FLAG_ENCRYPTED])
        + salt
        + nonce
        + struct.pack(">I", len(ciphertext))
        + ciphertext
    )
    tag = hmac.new(mac_key, body, hashlib.sha256).digest()
    return body + tag


def _read_header(reader) -> tuple[int, int]:
    """读取魔数与 flags，返回 (flags, 已消费字节数)。"""
    magic = reader.read(len(MAGIC))
    if magic != MAGIC:
        raise NoHiddenDataError("未检测到 VeilKit 隐写帧（魔数不匹配）")
    flags = reader.read(1)
    if len(flags) != 1:
        raise NoHiddenDataError("隐写帧不完整")
    return flags[0], len(MAGIC) + 1


def open_frame(reader, password: str | None) -> bytes:
    """从提供 ``read(n)`` 方法的比特/字节流中还原负载。

    reader 由 :mod:`veilkit.bitstream` 提供，按字节顺序吐出 LSB 还原出的数据。
    """
    flags, _ = _read_header(reader)

    if flags == 0:
        (length,) = struct.unpack(">I", reader.read(4))
        payload = reader.read(length)
        if len(payload) != length:
            raise NoHiddenDataError("隐写帧被截断")
        return payload

    if flags != _FLAG_ENCRYPTED:
        raise NoHiddenDataError(f"无法识别的帧标志位: 0x{flags:02x}")
    if not password:
        raise PasswordRequiredError("该载体中的内容已加密，请通过 -p/--password 提供口令")

    salt = reader.read(_SALT_LEN)
    nonce = reader.read(_NONCE_LEN)
    (length,) = struct.unpack(">I", reader.read(4))
    ciphertext = reader.read(length)
    tag = reader.read(_TAG_LEN)
    if len(salt) != _SALT_LEN or len(nonce) != _NONCE_LEN or len(tag) != _TAG_LEN:
        raise NoHiddenDataError("隐写帧被截断")
    if len(ciphertext) != length:
        raise NoHiddenDataError("密文长度不足，隐写帧被截断")

    enc_key, mac_key = _derive_keys(password, salt)
    expected_tag = hmac.new(
        mac_key,
        MAGIC
        + bytes([_FLAG_ENCRYPTED])
        + salt
        + nonce
        + struct.pack(">I", length)
        + ciphertext,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise AuthError("认证失败：口令错误或隐写数据已被篡改")
    return chacha20_xor(enc_key, nonce, ciphertext)


def frame_size(payload_len: int, encrypted: bool) -> int:
    """预测封装帧的总字节数，用于载体容量预检。"""
    if not encrypted:
        return len(MAGIC) + 1 + 4 + payload_len
    return len(MAGIC) + 1 + _SALT_LEN + _NONCE_LEN + 4 + payload_len + _TAG_LEN
