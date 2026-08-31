"""VeilKit 库 API 最小示例：把字节负载隐写进 PNG 并还原。

运行方式（无需安装，源码根目录下）：
    PYTHONPATH=src python3 examples/library_demo.py
"""

from veilkit import (
    capacity_human,
    hide_bytes,
    hide_text,
    reveal_bytes,
    reveal_text,
)
from veilkit.carriers.png import PNGImage


def main() -> None:
    # 1) 用代码生成一张 160x120 的载体 PNG（实际使用时换成任意 8-bit RGB/RGBA PNG）
    width, height = 160, 120
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            pixels += bytes([x & 0xFF, y & 0xFF, (x + y) & 0xFF])
    carrier = PNGImage(width, height, 3, pixels).render()

    # 2) 查看容量（加密帧会占用固定开销）
    info = capacity_human("png", carrier, encrypted=True)
    print("载体容量：", info["capacity_bytes"], "字节，最大加密负载：",
          info["max_payload_bytes"], "字节")

    # 3) 口令加密隐写（stego 即为可直接保存/发送的 PNG 字节串）
    secret = "这是一段需要保密并隐藏存在性的消息。".encode("utf-8")
    stego = hide_bytes("png", carrier, secret, password="my-passphrase")
    print("已生成隐写 PNG 字节串，大小", len(stego), "字节，视觉上与原图一致")

    # 4) 提取
    recovered = reveal_bytes("png", stego, "my-passphrase")
    print("提取结果：", recovered.decode("utf-8"))

    # 5) 零宽文本隐写
    hidden_text = hide_text("这是一段可以公开发布的封面文字。", "暗语：T-9",
                            password=None)
    print("文本隐写长度：", len(hidden_text), "（封面长度 16）")
    print("文本提取：", reveal_text(hidden_text).decode("utf-8"))


if __name__ == "__main__":
    main()
