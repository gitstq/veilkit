"""安全层测试：ChaCha20 RFC 8439 官方向量 + 帧封装/认证。"""

import unittest

from veilkit import crypto
from veilkit.crypto import chacha20_xor
from veilkit.errors import AuthError, NoHiddenDataError


class TestChaCha20RFC(unittest.TestCase):
    def test_rfc8439_section_2_3_2_block(self):
        """RFC 8439 第 2.3.2 节：单块密钥流向量。"""
        from veilkit.crypto import chacha20_block
        key = bytes(range(32))
        nonce = bytes.fromhex("000000090000004a00000000")
        expected = bytes.fromhex(
            "10f1e7e4d13b5915500fdd1fa32071c4"
            "c7d1f4c733c068030422aa9ac3d46c4e"
            "d2826446079faa0914c2d705d98b02a2"
            "b5129cd1de164eb9cbd083e8a2503c4e"
        )
        self.assertEqual(chacha20_block(key, 1, nonce), expected)

    """RFC 8439 第 2.4.2 节 Known-Answer-Test。"""

    def test_rfc8439_section_2_4_2(self):
        key = bytes(range(32))
        nonce = bytes.fromhex("000000000000004a00000000")
        plaintext = (
            b"Ladies and Gentlemen of the class of '99: If I could offer you "
            b"only one tip for the future, sunscreen would be it."
        )
        expected = bytes.fromhex(
            "6e2e359a2568f98041ba0728dd0d6981"
            "e97e7aec1d4360c20a27afccfd9fae0b"
            "f91b65c5524733ab8f593dabcd62b357"
            "1639d624e65152ab8f530c359f0861d8"
            "07ca0dbf500d6a6156a38e088a22b65e"
            "52bc514d16ccf806818ce91ab7793736"
            "5af90bbf74a35be6b40b8eedf2785e42"
            "874d"
        )
        ciphertext = chacha20_xor(key, nonce, plaintext, counter=1)
        self.assertEqual(ciphertext, expected)
        # 加解密同构
        self.assertEqual(chacha20_xor(key, nonce, ciphertext, counter=1), plaintext)


class TestFrame(unittest.TestCase):
    def test_plaintext_roundtrip(self):
        frame = crypto.seal(b"hello world", None)
        reader = crypto_open_reader(frame)
        self.assertEqual(crypto.open_frame(reader, None), b"hello world")

    def test_encrypted_roundtrip(self):
        frame = crypto.seal(b"secret payload", "pw123")
        self.assertEqual(crypto.open_frame(crypto_open_reader(frame), "pw123"),
                         b"secret payload")

    def test_wrong_password_rejected(self):
        frame = crypto.seal(b"secret payload", "right")
        with self.assertRaises(AuthError):
            crypto.open_frame(crypto_open_reader(frame), "wrong")

    def test_tamper_detected(self):
        frame = bytearray(crypto.seal(b"secret payload", "pw"))
        frame[-5] ^= 0x01  # 翻转密文/标签区比特
        with self.assertRaises(AuthError):
            crypto.open_frame(crypto_open_reader(bytes(frame)), "pw")

    def test_bad_magic(self):
        with self.assertRaises(NoHiddenDataError):
            crypto.open_frame(crypto_open_reader(b"XXXXXXXX" + b"\x00"), None)

    def test_frame_size_prediction(self):
        frame_plain = crypto.seal(b"a" * 100, None)
        frame_enc = crypto.seal(b"a" * 100, "pw")
        self.assertEqual(len(frame_plain), crypto.frame_size(100, False))
        self.assertEqual(len(frame_enc), crypto.frame_size(100, True))


def crypto_open_reader(data: bytes):
    from veilkit.core import _BytesReader
    return _BytesReader(data)


if __name__ == "__main__":
    unittest.main()
