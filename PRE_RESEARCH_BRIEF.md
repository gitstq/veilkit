# 项目预研简报（2026-08-31）

## 榜单信号
- GitHub 周榜/新锐榜出现 `nethical6/conversation-steganography`（Go，1240★，2026-07-17 创建，topic: steganography），隐写术（steganography）方向热度上升。
- 该项目依赖 LLM 把消息藏进"看起来正常的对话"，依赖大模型、在线服务，无法离线、确定性差、无法审计。

## 差异化机会
做一个**不依赖 LLM、完全离线、零第三方依赖、确定性可复现**的多载体隐写工具箱：
- 载体覆盖：PNG / BMP 图像 LSB、WAV 音频 LSB、零宽字符文本隐写；
- 安全层：PBKDF2-HMAC-SHA256 口令派生 + 纯标准库实现的 ChaCha20（RFC 8439）流加密 + HMAC-SHA256 加密后认证（encrypt-then-MAC），篡改/错口令可明确检出；
- 工程层：容量预检、清晰错误语义、CLI + 可导入库 + 离线 HTML 演示页。

## 去重校验（账号 gitstq 全量 1638 仓库）
- 关键词 stego/lsb/zero-width/covert/隐写：**0 命中**。
- 最接近项：PixelVault（对图片文件本身加密，非"载体中藏数据"）、HashForge-Lite（哈希/编码工具集）、FHEKit（同态加密）——核心场景与技术路径相似度均 < 30%，不构成重复。

## 结论
锁定目标：**VeilKit** —— 零依赖、本地优先的多载体隐写工具箱（Python CLI + Library + 离线演示页）。
