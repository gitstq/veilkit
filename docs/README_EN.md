# 🫥 VeilKit

**A zero-dependency, local-first multi-carrier steganography toolkit.**
Hide any file or text *invisibly* inside images, audio, or plain-looking messages — with optional
military-grade password encryption. Everything runs offline: nothing is uploaded, nothing is tracked.

🌐 **Language：** [简体中文](../README.md) ｜ [繁體中文](./README_zh-TW.md) ｜ [English](./README_EN.md)

<p align="center">
  <img alt="VeilKit architecture overview" src="./veilkit-arch-placeholder.png" width="640">
</p>

> 📸 *Demo GIF placeholder: `docs/demo.gif` — encrypt a file into a PNG and extract it back with a single command*

---

## 🎉 Introduction

**VeilKit** is a multi-carrier **steganography** toolkit implemented entirely with the Python
standard library. Unlike encryption, steganography hides the *existence* of communication:
an outsider only sees an ordinary picture, an audio clip, or a plain sentence — while the real
payload lives inside least-significant bits (LSB) or invisible Unicode characters, recoverable
only by someone who holds the carrier (and the password).

### 🎯 The problems it solves

- 😮‍💨 **Existing tools either pull in heavy dependencies or force you to upload files** — sending sensitive data to an unknown website never feels safe;
- 🧩 **Most open-source implementations support a single carrier** — PNG works, but audio or text means switching tools;
- 🔓 **Steganography without encryption**: once the hidden layer is detected, the payload is exposed — and most implementations have no tamper protection either;
- 🩹 **Image handling leans on heavy libraries like Pillow**, which is painful in offline, locked-down, or legacy environments.

### ✅ How VeilKit answers

| Dimension | VeilKit's choice |
|---|---|
| 🛡️ Privacy | **100% local**, zero network requests, no telemetry whatsoever |
| 🧱 Dependencies | **Zero runtime third-party dependencies** — stdlib only (ships its own PNG/WAV codecs) |
| 🧺 Carriers | PNG, BMP, WAV, and zero-width text behind **one unified CLI** |
| 🔐 Crypto | PBKDF2-SHA256 (200k rounds) + **ChaCha20 (RFC 8439)** + HMAC-SHA256 tamper protection |
| 🧪 Reliability | 32 tests, including the **official RFC vectors** for ChaCha20 and cross-decoding with Pillow |
| 💻 Platforms | Pure Python on Windows / macOS / Linux, Python ≥ 3.9 |

### 💡 Inspiration

The direction was inspired by a recently trending LLM conversation-steganography project: it showed
how strong the demand for "hiding information inside everyday carriers" really is. That approach,
however, depends on online LLM services, is non-deterministic, and resists auditing. VeilKit takes
the opposite path — **deterministic algorithms, fully offline, cryptographically auditable, and with
broader carrier coverage**. It is 100% original code; no existing project's source was copied.

> ⚖️ **Responsible use:** VeilKit is meant for privacy protection, digital watermarking, CTF
> education, and non-destructive forensics exercises. Do not use it to break the law in your
> jurisdiction.

---

## ✨ Features

### 🖼️ Multi-carrier LSB steganography
- **PNG**: a hand-written stdlib decoder that reverses all five row filters
  (None/Sub/Up/Average/Paeth). Only the LSB of R/G/B channels changes, while the **alpha channel is
  left untouched**. Output files open in every image viewer;
- **BMP**: 24-bit uncompressed bitmaps; headers and row padding are preserved byte-for-byte;
- **WAV**: PCM 8/16-bit mono/stereo — only the samples' LSBs change (inaudible), other RIFF chunks stay intact.

### 🔤 Zero-width text steganography
- Hides content inside any sentence using *visually invisible* characters
  (`U+200B/U+200C/U+200D/U+2060`);
- Travels through chat apps, documents, and code comments without any visible trace;
- Dual extraction strategy (**block markers + full-scan fallback**) plus a one-command `text-strip` cleaner.

### 🔐 Cryptographic security layer (optional, recommended)
- **PBKDF2-HMAC-SHA256** with 200,000 iterations and a fresh 16-byte random salt to resist brute force;
- **ChaCha20 stream cipher** (RFC 8439), implemented in pure stdlib and verified against official KAT vectors;
- **Encrypt-then-MAC**: HMAC-SHA256 covers header and ciphertext — a wrong password or a single flipped bit is rejected outright;
- A fresh random salt and nonce on every write: the same payload never produces the same output twice (anti-replay).

### 📏 Capacity pre-checks and explicit errors
- Carrier capacity is computed *before* writing (`capacity` command), so a carrier is **never left half-written**;
- Unsupported bit depth / color type / compression raises an actionable message instead of an obscure stack trace.

### 🧰 Two ways to use it: CLI and library
- A full-featured command line with pipes, `VEILKIT_PASSWORD` env var, and secure hidden terminal prompts;
- A small, stable Python API you can embed directly in your own programs.

### 🖥️ Bonus offline playground
- `examples/zero-width-playground.html` is a single-file page — **double-click to open, works with the network unplugged**;
- Its plaintext frame format is **bidirectionally interoperable** with the CLI (verified with Node ↔ Python).

---

## 🚀 Quick Start

### 📋 Requirements

- Python **3.9 – 3.13** (standard library only; no internet or package installation needed at runtime)
- Works on Windows, macOS, and Linux

### 📦 Installation

```bash
# Option 1 — pip (recommended; installs the `veilkit` command)
pip install veilkit

# Option 2 — run straight from source (no installation)
git clone https://github.com/gitstq/veilkit.git
cd veilkit
PYTHONPATH=src python3 -m veilkit version
```

### 🌱 30-second tour

```bash
# 1️⃣ Encrypt secret.txt with a password and hide it inside photo.png → stego.png
veilkit hide -i photo.png -s secret.txt -o stego.png -p "your-strong-passphrase"

# 2️⃣ Extract and decrypt stego.png back into recovered.txt
veilkit extract -i stego.png -o recovered.txt -p "your-strong-passphrase"

# 3️⃣ Check how much a carrier can hold
veilkit capacity -i photo.png --encrypted

# 4️⃣ Text mode: bury a secret inside an innocent-looking sentence
veilkit text-hide --cover "Leaving work at six as usual" --secret "Meet at the east gate" -p pw -o msg.txt
veilkit text-extract -i msg.txt -p pw --as-text
```

> 🔑 Don't want the password in your shell history? Omit `-p` and VeilKit prompts for it securely.
> In automation, use the `VEILKIT_PASSWORD` environment variable.

---

## 📖 Usage Guide

### 🧾 Command reference

| Command | Purpose |
|---|---|
| `veilkit hide` | Embed a payload in a PNG/BMP/WAV carrier |
| `veilkit extract` | Recover a payload from a PNG/BMP/WAV carrier |
| `veilkit capacity` | Report carrier capacity and payload ceiling |
| `veilkit text-hide` | Zero-width text steganography |
| `veilkit text-extract` | Extract zero-width-hidden content |
| `veilkit text-strip` | Remove zero-width markers from text |
| `veilkit version` | Print the version |

### 🖼️ Binary carriers (PNG / BMP / WAV)

```bash
# Unencrypted (hides existence only — no confidentiality)
veilkit hide -i demo.bmp --secret "plain marker" -o marked.bmp
veilkit extract -i marked.bmp

# Encrypt and hide any binary file (zip, documents, keys, …)
veilkit hide -i song.wav -s evidence.zip -o song.stego.wav -p "S3cret!"
veilkit extract -i song.stego.wav -p "S3cret!" -o evidence.zip

# Force the carrier type when the extension is missing or ambiguous
veilkit hide --type png -i no_extension_file -s note.txt -o out.png
```

#### Support matrix

| Carrier | Supported | Rejected with a clear error |
|---|---|---|
| PNG | 8-bit, RGB(2)/RGBA(6), non-interlaced | Palette, 16-bit, Adam7 interlace |
| BMP | BITMAPINFOHEADER, 24-bit, BI_RGB | Compressed BMP, 8/32-bit with palette |
| WAV | PCM (format=1), 8/16-bit, any channel count | Float PCM, ADPCM, MP3-in-WAV |

> 💡 Convert unsupported variants to the standard form first (e.g. Paint, Audacity, or ffmpeg).

### 🔤 Zero-width text

```bash
# Three insertion points: end (default) / start / split (at the first whitespace)
veilkit text-hide --cover-file cover.txt -s secret.md --position split -o out.txt -p pw

# Read the carrier from a pipe
cat out.txt | veilkit text-extract -p pw --as-text

# Scrub hidden markers and recover the clean cover text
veilkit text-strip -i out.txt
```

### 🐍 Python library API

```python
from veilkit import hide_bytes, reveal_bytes, hide_text, reveal_text, capacity_human

# 1) Image steganography (carrier is PNG bytes)
stego = hide_bytes("png", carrier_bytes, b"hello", password="pw")
assert reveal_bytes("png", stego, password="pw") == b"hello"

# 2) Inspect capacity
print(capacity_human("png", carrier_bytes, encrypted=True))

# 3) Text steganography
msg = hide_text("An ordinary sentence.", "secret phrase", password=None)
print(reveal_text(msg).decode("utf-8"))   # secret phrase
```

See [`examples/library_demo.py`](../examples/library_demo.py) for a complete runnable example.

### 🖥️ Offline web playground

Double-click [`examples/zero-width-playground.html`](../examples/zero-width-playground.html) —
no server and no network required. Its plaintext frames interoperate with the CLI:

```bash
# Text produced by the web page can be extracted directly with the CLI
# (the page supports plaintext mode only; use the CLI for encrypted frames)
veilkit text-extract -i webpage_output.txt --as-text
```

### 🎬 Typical use cases

- 🧬 **Offline digital watermarking** — embed author IDs or purchase numbers in deliverable images for leak tracing;
- 📻 **Transport over watched channels** — combine with a password to move key shards or recovery seeds inside ordinary pictures;
- 🚩 **CTF / security training** — teach the layered relationship between LSB, zero-width text, encryption, and steganography;
- 🗂️ **Private local archives** — keep private notes inside your own photo library, stored locally, never uploaded.

### ❓ FAQ

**Can anyone tell the image was modified?**
LSB changes each color channel by at most ±1 — well below the threshold of screens and the human eye.
Cross-validation with Pillow confirms a maximum per-channel delta of 1. However, **never apply lossy
compression after embedding** (JPEG, resampling, or audio transcoding destroys LSB data).

**Is steganography the same as encryption?**
No. Steganography hides *that a secret exists*; encryption hides *what it says*. VeilKit recommends
stacking both (pass `-p`) for defense in depth.

**Can I recover the payload if I forget the password?**
No, by design. A failed HMAC check aborts decryption; there is no backdoor.

**How large a payload fits?**
Roughly: PNG ≈ width×height×3 / 8 bytes; WAV ≈ total sample count / 8 bytes. Use `capacity` for exact numbers.

---

## 💡 Design Notes & Roadmap

### 🧠 Principles

1. **Local-first** — data never leaves the machine, and no capability depends on the network;
2. **Zero dependencies as a security feature** — minimal supply-chain surface; cryptographic correctness is proven with RFC vectors;
3. **Pre-check, then write** — insufficient capacity aborts cleanly; half-written files never happen;
4. **Fail loudly** — every error is a typed exception; errors are never swallowed silently.

### 🧱 Architecture

```
veilkit/
├── cli.py              # argparse CLI layer
├── core.py             # Orchestration: carrier ↔ framing ↔ capacity checks
├── crypto.py           # ChaCha20 (RFC 8439) + PBKDF2 + HMAC framing
├── bitstream.py        # Bytes ↔ MSB-first bit stream
└── carriers/
    ├── png.py          # Stdlib PNG decode/re-encode + LSB
    ├── bmp.py          # 24-bit BMP + LSB (in-place structure preserved)
    ├── wav.py          # PCM WAV + LSB
    └── text.py         # Zero-width Unicode text steganography
```

### 🗺️ Roadmap

- [ ] v1.1: lossless GIF frames and FLAC carriers; PNG palette-mode support
- [ ] v1.2: experimental frequency-domain (DCT) embedding resilient to re-encoding
- [ ] v1.3: batch directory processing and steganalysis helpers
- [ ] v2.0: optional Shamir secret sharing — extraction requires multiple key holders

Ideas for new carriers and use cases are welcome in Issues.

---

## 📦 Packaging & Deployment

VeilKit is a **library / CLI project**: Python itself provides cross-platform support, so no
per-OS binaries are required.

### Build a wheel / sdist

```bash
# Linux / macOS
make test && make wheel          # artifacts land in dist/
bash scripts/build.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\build.ps1

# Manual (identical on every platform)
python -m pip wheel . --no-deps -w dist
```

### Verify the install in an isolated environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install dist/veilkit-*.whl
veilkit version
```

### Compatibility

- Runtime: Python 3.9+, OS-independent;
- Outputs are standard PNG/BMP/WAV/UTF-8 text files that open in any ordinary software;
- Password frames are cross-platform by construction (fixed big-endian framing + standard algorithms):
  embed on Windows, extract on Linux/macOS.

---

## 🤝 Contributing

Issues, pull requests, and documentation improvements are welcome! Read the full
[CONTRIBUTING.md](../CONTRIBUTING.md) before submitting:

- 🌿 Branch names: `feat/xxx`, `fix/xxx`, `docs/xxx`;
- 📝 Angular-style commits: `feat: ...` / `fix: ...` / `docs: ...` / `refactor: ...` / `test: ...`;
- ✅ `make test` must pass; new features need roundtrip and error-path tests;
- 🚫 PRs introducing runtime third-party dependencies won't be accepted (open an Issue first to discuss).

---

## 📄 License

Released under the [MIT License](../LICENSE). Free for personal and commercial use, provided the
copyright and permission notice are retained and applicable laws are respected.

<p align="center">🫥 <b>VeilKit</b> — keep secrets invisible, and privacy in your own hands.</p>
