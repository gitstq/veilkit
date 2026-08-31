# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/) 与 Keep a Changelog 约定。

## [1.0.0] - 2026-08-31

### 🎉 首次发布

- ✨ 支持 **PNG**（8-bit RGB/RGBA，纯标准库解码全部 5 种行滤波器并重编码）LSB 隐写；
- ✨ 支持 **BMP**（24-bit BI_RGB，保留文件头与行填充）LSB 隐写；
- ✨ 支持 **WAV**（PCM 8/16-bit、单/立体声，保留其他 RIFF 块）LSB 隐写；
- ✨ 支持**零宽字符文本隐写**（ZWSP/ZWNJ/ZWJ + 块边界，支持封面文本与清除）；
- 🔐 安全层：PBKDF2-HMAC-SHA256（200,000 轮）口令派生、纯标准库 ChaCha20（RFC 8439）
  流加密、HMAC-SHA256 encrypt-then-MAC 完整性认证，错口令/篡改可明确检出；
- 🧰 完整 CLI：`hide / extract / capacity / text-hide / text-extract / text-strip / version`；
- 🧩 稳定库 API：`hide_bytes / reveal_bytes / hide_text / reveal_text / capacity_human`；
- 🖥️ 附带完全离线的单文件零宽字符演练页 `examples/zero-width-playground.html`，
  与 CLI 明文帧双向互通；
- ✅ 32 项单元/端到端测试，含 ChaCha20 RFC 8439 §2.3.2 / §2.4.2 官方测试向量、
  Pillow 交叉解码验证；
- 📦 零运行时第三方依赖，Python ≥ 3.9，跨 Windows/macOS/Linux。
