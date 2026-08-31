# 🫥 VeilKit · 隐纱匣

**零依赖 · 本地优先 · 多载体隐写工具箱**
把任意文件或文本"隐形"藏进图片、音频与普通文字中，可选军用级口令加密，全程离线、不上传、不留痕。

🌐 **语言切换 / Language：** [简体中文](./README.md) ｜ [繁體中文](./docs/README_zh-TW.md) ｜ [English](./docs/README_EN.md)

<p align="center">
  <img alt="VeilKit 架构示意占位" src="./docs/veilkit-arch-placeholder.png" width="640">
</p>

> 📸 *演示动图占位：`docs/demo.gif` —— 一条命令把加密文件藏进 PNG，再原样提取*

---

## 🎉 项目介绍

**VeilKit（隐纱匣）** 是一个纯 Python 标准库实现的多载体**隐写术（Steganography）**工具箱。
与"加密"不同，隐写追求的是**隐藏通信本身的存在**：外人看到的只是一张普通图片、一段录音或一句平常的话，
而真正的内容以最低有效位（LSB）或零宽字符的形式潜伏其中，只有持有载体与口令的人才能提取。

### 🎯 它解决什么痛点

- 😮‍💨 **现成工具要么装一堆依赖，要么必须联网上传**——敏感文件交给陌生网站始终不放心；
- 🧩 **多数开源实现只支持单一载体**，PNG 能藏、音频/文本就得换工具；
- 🔓 **只隐写不加密**：一旦被识别出隐写，内容直接裸奔；多数实现也没有防篡改校验；
- 🩹 **PNG 处理强依赖 Pillow 等重依赖**，老旧/离线/受限环境装不动。

### ✅ VeilKit 的回答

| 维度 | VeilKit 的选择 |
|---|---|
| 🛡️ 隐私 | **100% 本地运行**，零网络请求，不收集任何遥测 |
| 🧱 依赖 | **运行时零第三方依赖**，仅用 Python 标准库（自带 PNG/WAV 编解码器） |
| 🧺 载体 | PNG、BMP、WAV、零宽文本，**一套命令统一处理** |
| 🔐 加密 | PBKDF2-SHA256（20 万轮）+ **ChaCha20（RFC 8439）** + HMAC-SHA256 防篡改 |
| 🧪 可靠 | 32 项测试，含 ChaCha20 **RFC 官方测试向量**与 Pillow 交叉解码验证 |
| 💻 平台 | 纯 Python，Windows / macOS / Linux 通用，Python ≥ 3.9 |

### 💡 灵感来源

项目方向受 GitHub 近期走热的 LLM 对话隐写项目启发：它证明了"把信息藏进日常载体"这一需求的旺盛生命力，
但其依赖大模型在线服务、结果不确定、无法审计。VeilKit 走了一条相反的路——
**确定性算法、完全离线、密码学可审计、载体覆盖更广**，并 100% 自研实现，未复制任何现有项目代码。

> ⚖️ **合规提示**：VeilKit 面向隐私保护、数字水印、CTF 教学、无损取证演练等合法用途，
> 请勿用于违反法律法规的场景。

---

## ✨ 核心特性

### 🖼️ 多载体 LSB 隐写
- **PNG**：纯标准库手写解码器，支持逆向全部 5 种行滤波器（None/Sub/Up/Average/Paeth），
  只改 R/G/B 通道最低位，**Alpha 通道原样保留**，输出文件可被任意看图软件打开；
- **BMP**：24-bit 未压缩位图，文件头与行填充逐字节保留；
- **WAV**：PCM 8/16-bit、单/立体声，只动采样最低位，人耳不可闻，其他 RIFF 块原样保留。

### 🔤 零宽字符文本隐写
- 利用 `U+200B/U+200C/U+200D/U+2060` 等**视觉不可见字符**，把内容藏进任何一句话；
- 可在聊天框、文档、代码注释中传播，肉眼完全无感；
- 自带**块边界 + 全扫描回退**双提取策略，并提供 `text-strip` 一键清除。

### 🔐 密码学安全层（可选但默认推荐）
- **PBKDF2-HMAC-SHA256**，200,000 轮迭代、16 字节随机盐，抗暴力破解；
- **ChaCha20 流密码**（RFC 8439，纯标准库实现并通过官方 KAT 向量）；
- **Encrypt-then-MAC**：HMAC-SHA256 覆盖帧头与密文，**错口令、改一个比特都会被明确拦截**；
- 每次写入随机盐 + 随机 nonce，同一内容两次隐写结果不同，抗重放识别。

### 📏 容量预检与清晰错误语义
- 写入前自动计算载体容量（`capacity` 子命令），**绝不写一半失败损坏载体**；
- 不支持的位深/色彩类型/压缩格式会给出可操作的中文错误，而不是神秘堆栈。

### 🧰 双形态：CLI + Library
- 命令行覆盖全部能力，支持管道、环境变量口令（`VEILKIT_PASSWORD`）、终端安全输入；
- 同时提供简洁稳定的 Python 库 API，可直接嵌入你自己的程序。

### 🖥️ 附赠离线演练页
- `examples/zero-width-playground.html` 单文件网页，**双击即开、断网可用**；
- 与 CLI 的明文帧格式**双向互通**（已用 Node ↔ Python 交叉验证）。

---

## 🚀 快速开始

### 📋 环境要求

- Python **3.9 ~ 3.13**（仅标准库，无需联网安装任何依赖）
- Windows / macOS / Linux 均可

### 📦 安装

```bash
# 方式一：pip 安装（推荐，获得 veilkit 命令）
pip install veilkit

# 方式二：源码直接运行（零安装）
git clone https://github.com/gitstq/veilkit.git
cd veilkit
PYTHONPATH=src python3 -m veilkit version
```

### 🌱 30 秒上手

```bash
# 1️⃣ 把 secret.txt 用口令加密后藏进 photo.png，输出 stego.png
veilkit hide -i photo.png -s secret.txt -o stego.png -p "你的强口令"

# 2️⃣ 从 stego.png 提取并解密，还原为 recovered.txt
veilkit extract -i stego.png -o recovered.txt -p "你的强口令"

# 3️⃣ 先看看一张图最多能藏多少
veilkit capacity -i photo.png --encrypted

# 4️⃣ 文本隐写：把密语藏进一句普通的话
veilkit text-hide --cover "今晚正常下班" --secret "东门见" -p pw -o msg.txt
veilkit text-extract -i msg.txt -p pw --as-text
```

> 🔑 不想把口令写进命令？省略 `-p`，VeilKit 会在终端安全地隐式询问；
> 自动化场景可使用环境变量 `VEILKIT_PASSWORD`。

---

## 📖 详细使用指南

### 🧾 全部命令一览

| 命令 | 作用 |
|---|---|
| `veilkit hide` | 向 PNG/BMP/WAV 写入隐写内容 |
| `veilkit extract` | 从 PNG/BMP/WAV 提取隐写内容 |
| `veilkit capacity` | 计算载体容量与负载上限 |
| `veilkit text-hide` | 零宽字符文本隐写 |
| `veilkit text-extract` | 提取零宽字符隐写内容 |
| `veilkit text-strip` | 清除文本中的零宽隐写符号 |
| `veilkit version` | 查看版本 |

### 🖼️ 二进制载体（PNG / BMP / WAV）

```bash
# 不加密（仅隐藏存在性，不提供保密性）
veilkit hide -i demo.bmp --secret "一段明文标记" -o marked.bmp
veilkit extract -i marked.bmp

# 加密隐藏任意二进制文件（zip、文档、密钥……）
veilkit hide -i song.wav -s evidence.zip -o song.stego.wav -p "S3cret!"
veilkit extract -i song.stego.wav -s evidence.zip -p "S3cret!"   # 注意：-o 指定输出
veilkit extract -i song.stego.wav -p "S3cret!" -o evidence.zip

# 类型无法从扩展名判断时显式指定
veilkit hide --type png -i no_extension_file -s note.txt -o out.png
```

#### 支持矩阵

| 载体 | 支持格式 | 不支持（会明确报错） |
|---|---|---|
| PNG | 8-bit、RGB(2)/RGBA(6)、非隔行 | 调色板、16-bit、Adam7 隔行 |
| BMP | BITMAPINFOHEADER、24-bit、BI_RGB | 压缩 BMP、8/32-bit 带调色板 |
| WAV | PCM(format=1)、8/16-bit、任意声道数 | 浮点 PCM、ADPCM、MP3 封装 |

> 💡 不支持的格式可用系统自带画图、Audacity、ffmpeg 等另存为标准格式后再处理。

### 🔤 文本零宽隐写

```bash
# 三种插入位置：end（默认，文末）/ start（文首）/ split（首个空格处）
veilkit text-hide --cover-file cover.txt -s secret.md --position split -o out.txt -p pw

# 直接从标准输入读取待分析文本
cat out.txt | veilkit text-extract -p pw --as-text

# 清除隐写符号，得到干净封面
veilkit text-strip -i out.txt
```

### 🐍 Python 库 API

```python
from veilkit import hide_bytes, reveal_bytes, hide_text, reveal_text, capacity_human

# 1) 图片隐写（carrier 为 PNG 字节串）
stego = hide_bytes("png", carrier_bytes, b"hello", password="pw")
assert reveal_bytes("png", stego, password="pw") == b"hello"

# 2) 查看容量
print(capacity_human("png", carrier_bytes, encrypted=True))

# 3) 文本隐写
msg = hide_text("这是一句普通的话", "暗语", password=None)
print(reveal_text(msg).decode("utf-8"))   # 暗语
```

完整可运行示例见 [`examples/library_demo.py`](./examples/library_demo.py)。

### 🖥️ 离线网页演练场

双击打开 [`examples/zero-width-playground.html`](./examples/zero-width-playground.html)，
无需服务器、无需联网即可体验文本隐写；其帧格式与 CLI 明文模式互通：

```bash
# 网页生成的文本，CLI 可直接提取（网页仅支持明文模式，加密请用 CLI）
veilkit text-extract -i webpage_output.txt --as-text
```

### 🎬 典型场景

- 🧬 **离线数字水印**：把作者标识/采购编号藏进交付图片，泄露时可溯源；
- 📻 **敏感信道传输**：配合口令加密，把密钥分片/助记词藏进普通图片传输；
- 🚩 **CTF / 安全教学**：讲解 LSB、零宽字符、加密与隐写的分层关系；
- 🗂️ **个人隐私归档**：把私密备注藏进自己的照片库，本地保存不上云。

### ❓ 常见问题

**Q：隐写后的图片会被看出来吗？**
A：LSB 只改每个颜色通道 ±1 的亮度差，远低于显示设备与肉眼分辨阈值；经 Pillow 交叉验证，
隐写前后单通道最大差值为 1。但**不要对隐写后的文件再做有损压缩**（JPEG、重采样、音频转码都会破坏 LSB）。

**Q：隐写等于加密吗？**
A：不等于。隐写隐藏"有秘密"这件事，加密隐藏"秘密是什么"。VeilKit 默认建议两者叠加（加 `-p`），
形成纵深防护。

**Q：忘记口令还能找回吗？**
A：不能，这是刻意设计。HMAC 校验失败即拒绝解密，没有后门。

**Q：最大能藏多大？**
A：粗略估算：PNG ≈ 宽×高×3 / 8 字节；WAV ≈ 采样总数 / 8 字节；精确值请用 `capacity` 命令。

---

## 💡 设计思路与迭代规划

### 🧠 设计理念

1. **本地优先（Local-first）**：数据不出机器，能力不依赖网络；
2. **零依赖即安全**：供应链攻击面最小化，密码学实现用 RFC 向量自证正确；
3. **先预检、后写入**：容量不足直接拒绝，绝不产生半截损坏文件；
4. **失败要响亮**：所有错误走类型化异常，禁止静默吞错。

### 🧱 技术架构

```
veilkit/
├── cli.py              # argparse 命令行层
├── core.py             # 编排：载体选择 ↔ 帧封装 ↔ 容量预检
├── crypto.py           # ChaCha20(RFC8439) + PBKDF2 + HMAC 帧
├── bitstream.py        # 字节 ↔ MSB-first 比特流
└── carriers/
    ├── png.py          # 纯标准库 PNG 解码/重编码 + LSB
    ├── bmp.py          # 24-bit BMP + LSB（原位保留文件结构）
    ├── wav.py          # PCM WAV + LSB
    └── text.py         # 零宽 Unicode 文本隐写
```

### 🗺️ 迭代路线图

- [ ] v1.1：GIF 无损帧、FLAC 无损音频载体；PNG 调色板模式支持
- [ ] v1.2：抗重编码的频域（DCT）图片隐写实验模式
- [ ] v1.3：批量目录处理与隐写检测（steganalysis）辅助工具
- [ ] v2.0：可选的 Shamir 门限分片，多人持钥才能提取

欢迎在 Issue 区提出你想要的载体与场景。

---

## 📦 打包与部署指南

VeilKit 属于**工具库 / CLI 类项目**，跨平台由 Python 自身保证，无需为每个操作系统单独打包二进制。

### 构建 wheel / sdist

```bash
# Linux / macOS
make test && make wheel          # 产物输出到 dist/
bash scripts/build.sh

# Windows（PowerShell）
powershell -ExecutionPolicy Bypass -File scripts\build.ps1

# 手动方式（全平台一致）
python -m pip wheel . --no-deps -w dist
```

### 隔离环境验证安装

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install dist/veilkit-*.whl
veilkit version
```

### 兼容性说明

- 运行环境：Python 3.9+，操作系统无关；
- 输出文件为标准 PNG/BMP/WAV/UTF-8 文本，可被任意常规软件打开；
- 口令帧跨平台一致（大端定长帧 + 标准算法），在 Windows 写入的载体可在 Linux/macOS 提取。

---

## 🤝 贡献指南

我们欢迎 Issue、PR 与文档改进！提交前请阅读完整的 [CONTRIBUTING.md](./CONTRIBUTING.md)：

- 🌿 分支命名：`feat/xxx`、`fix/xxx`、`docs/xxx`；
- 📝 提交信息遵循 Angular 规范：`feat: ...` / `fix: ...` / `docs: ...` / `refactor: ...` / `test: ...`；
- ✅ `make test` 全部通过，新增能力必须补往返测试与异常路径测试；
- 🚫 不接受引入运行时第三方依赖的 PR（请先开 Issue 讨论）。

---

## 📄 开源协议

本项目基于 [MIT License](./LICENSE) 开源，可自由用于个人与商业用途，
但请保留版权与许可声明，并遵守所在地区的法律法规。

<p align="center">🫥 <b>VeilKit</b> —— 让秘密归于无形，让隐私握在自己手里。</p>
