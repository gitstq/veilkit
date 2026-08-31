"""CLI 端到端测试：以子进程方式运行 python -m veilkit。"""

import os
import struct
import subprocess
import sys
import tempfile
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))


def make_png_file(path: str, width: int, height: int) -> None:
    sys.path.insert(0, SRC_DIR)
    from veilkit.carriers.png import PNGImage  # noqa: E402

    pixels = bytes((i * 37 + 11) & 0xFF for i in range(width * height * 3))
    with open(path, "wb") as handle:
        handle.write(PNGImage(width, height, 3, bytearray(pixels)).render())


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.env = {**os.environ, "PYTHONPATH": SRC_DIR}

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, input_bytes=None):
        return subprocess.run(
            [sys.executable, "-m", "veilkit", *args],
            capture_output=True, env=self.env, input=input_bytes, timeout=60,
        )

    def test_png_hide_extract_file(self):
        carrier = os.path.join(self.dir, "c.png")
        stego = os.path.join(self.dir, "s.png")
        secret = os.path.join(self.dir, "secret.bin")
        out = os.path.join(self.dir, "out.bin")
        make_png_file(carrier, 64, 64)
        with open(secret, "wb") as handle:
            handle.write(b"command-line roundtrip \x00\x01\x02")
        r1 = self.run_cli("hide", "-i", carrier, "-s", secret, "-o", stego,
                          "-p", "pass")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        r2 = self.run_cli("extract", "-i", stego, "-o", out, "-p", "pass")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        with open(secret, "rb") as a, open(out, "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_wrong_password_exit_code(self):
        carrier = os.path.join(self.dir, "c.png")
        stego = os.path.join(self.dir, "s.png")
        make_png_file(carrier, 64, 64)
        self.run_cli("hide", "-i", carrier, "--secret", "hi", "-o", stego,
                     "-p", "right")
        r = self.run_cli("extract", "-i", stego, "-p", "wrong")
        self.assertEqual(r.returncode, 1)
        self.assertIn("认证失败", r.stderr.decode())

    def test_capacity_command(self):
        carrier = os.path.join(self.dir, "c.png")
        make_png_file(carrier, 32, 16)
        r = self.run_cli("capacity", "-i", carrier, "--encrypted")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = r.stdout.decode()
        self.assertIn("最大负载", text)

    def test_text_hide_extract_pipeline(self):
        stego = os.path.join(self.dir, "stego.txt")
        out = os.path.join(self.dir, "out.txt")
        r1 = self.run_cli("text-hide", "--cover", "Visible cover content",
                          "--secret", "隐藏消息", "-o", stego, "-p", "pw")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        r2 = self.run_cli("text-extract", "-i", stego, "-o", out,
                          "-p", "pw", "--as-text")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        with open(out, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "隐藏消息")

    def test_text_strip(self):
        r = self.run_cli("text-strip", "--text", "a\u200b\u200cb")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.decode().strip(), "ab")

    def test_version(self):
        r = self.run_cli("version")
        self.assertEqual(r.returncode, 0)
        self.assertIn("VeilKit", r.stdout.decode())


if __name__ == "__main__":
    unittest.main()
