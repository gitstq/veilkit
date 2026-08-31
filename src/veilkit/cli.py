"""VeilKit 命令行界面。

子命令一览::

    hide          向 PNG/BMP/WAV 载体写入隐写内容
    extract       从 PNG/BMP/WAV 载体提取隐写内容
    capacity      评估载体可承载的负载上限
    text-hide     向文本写入零宽字符隐写内容
    text-extract  从文本提取零宽字符隐写内容
    text-strip    清除文本中的零宽隐写符号
    version       输出版本号
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from . import __version__
from .carriers import text as text_carrier
from .core import (
    SUPPORTED_BINARY_TYPES,
    capacity_human,
    detect_type,
    hide_bytes,
    hide_text,
    reveal_bytes,
    reveal_text,
)
from .errors import PasswordRequiredError, VeilKitError


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _resolve_password(cli_password: str | None) -> str | None:
    """口令优先级：参数 > 环境变量 VEILKIT_PASSWORD > 终端安全输入。"""
    if cli_password is not None:
        return cli_password
    env_password = os.environ.get("VEILKIT_PASSWORD")
    if env_password is not None:
        return env_password
    if sys.stdin.isatty():
        return getpass.getpass("🔑 请输入隐写口令（留空表示不加密）: ") or None
    return None


def _read_binary(path: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise VeilKitError(f"无法读取文件 {path}: {exc}") from exc


def _write_binary(path: str | None, data: bytes) -> None:
    if path:
        with open(path, "wb") as handle:
            handle.write(data)
    else:
        sys.stdout.buffer.write(data)


def _read_secret(args) -> bytes:
    if getattr(args, "secret_file", None):
        return _read_binary(args.secret_file)
    if getattr(args, "secret", None) is not None:
        return args.secret.encode("utf-8")
    raise VeilKitError("必须通过 -s/--secret-file 或 --secret 提供待隐藏内容")


def _resolve_kind(args, path: str) -> str:
    if getattr(args, "type", None):
        return args.type
    return detect_type(path)


def _write_text(path: str | None, text: str) -> None:
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------

def cmd_hide(args) -> int:
    carrier = _read_binary(args.input)
    kind = _resolve_kind(args, args.input)
    payload = _read_secret(args)
    password = _resolve_password(args.password)
    result = hide_bytes(kind, carrier, payload, password=password)
    _write_binary(args.output, result)
    if args.output:
        mode = "加密隐写" if password else "普通隐写"
        print(f"✅ {mode}完成：{len(payload)} 字节负载已写入 {args.output}（载体: {kind}）")
    return 0


def cmd_extract(args) -> int:
    carrier = _read_binary(args.input)
    kind = _resolve_kind(args, args.input)
    password = _resolve_password(args.password)
    try:
        payload = reveal_bytes(kind, carrier, password=password)
    except PasswordRequiredError:
        password = _resolve_password(None)
        payload = reveal_bytes(kind, carrier, password=password)
    _write_binary(args.output, payload)
    if args.output:
        print(f"✅ 已提取 {len(payload)} 字节到 {args.output}")
    return 0


def cmd_capacity(args) -> int:
    carrier = _read_binary(args.input)
    kind = _resolve_kind(args, args.input)
    info = capacity_human(kind, carrier, encrypted=bool(args.encrypted))
    print(f"载体类型     : {info['type']}")
    print(f"可写比特数   : {info['capacity_bits']:,} bit")
    print(f"可写字节数   : {info['capacity_bytes']:,} B")
    print(f"帧封装开销   : {info['frame_overhead_bytes']} B"
          f"（{'加密模式' if info['encrypted'] else '明文模式'}）")
    print(f"最大负载     : {info['max_payload_bytes']:,} B")
    return 0


def _read_cover(args) -> str:
    if getattr(args, "cover_file", None):
        with open(args.cover_file, "r", encoding="utf-8") as handle:
            return handle.read()
    return args.cover or ""


def cmd_text_hide(args) -> int:
    cover = _read_cover(args)
    if args.secret_file:
        payload = _read_binary(args.secret_file)
    else:
        payload = (args.secret or "").encode("utf-8")
    password = _resolve_password(args.password)
    result = hide_text(cover, payload, password=password, position=args.position)
    _write_text(args.output, result)
    if args.output:
        print(f"✅ 文本隐写完成，输出到 {args.output}（封面 {len(cover)} 字符，"
              f"负载 {len(payload)} 字节）")
    return 0


def _read_text_input(args) -> str:
    if getattr(args, "input", None):
        with open(args.input, "r", encoding="utf-8") as handle:
            return handle.read()
    if getattr(args, "text", None) is not None:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise VeilKitError("文本模式需要通过 -i 文件、--text 或管道提供输入")


def cmd_text_extract(args) -> int:
    stego_text = _read_text_input(args)
    password = _resolve_password(args.password)
    try:
        payload = reveal_text(stego_text, password=password)
    except PasswordRequiredError:
        password = _resolve_password(None)
        payload = reveal_text(stego_text, password=password)
    if args.as_text:
        _write_text(args.output, payload.decode("utf-8"))
    else:
        _write_binary(args.output, payload)
    if args.output:
        print(f"✅ 已提取 {len(payload)} 字节到 {args.output}")
    return 0


def cmd_text_strip(args) -> int:
    text = _read_text_input(args)
    _write_text(args.output, text_carrier.strip(text))
    return 0


def cmd_version(_args) -> int:
    print(f"VeilKit {__version__}")
    return 0


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="veilkit",
        description="VeilKit —— 零依赖、本地优先的多载体隐写工具箱（PNG/BMP/WAV/文本）",
    )
    parser.add_argument("--debug", action="store_true", help="出错时打印完整堆栈")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hide = sub.add_parser("hide", help="向二进制载体写入隐写内容")
    p_hide.add_argument("-i", "--input", required=True, help="载体文件路径（.png/.bmp/.wav）")
    p_hide.add_argument("-o", "--output", help="输出文件路径（缺省输出到标准输出）")
    secret_group = p_hide.add_mutually_exclusive_group()
    secret_group.add_argument("-s", "--secret-file", help="待隐藏内容的文件路径")
    secret_group.add_argument("--secret", help="直接传入待隐藏文本")
    p_hide.add_argument("-p", "--password", help="加密口令（也可用环境变量 VEILKIT_PASSWORD）")
    p_hide.add_argument("--type", choices=SUPPORTED_BINARY_TYPES,
                        help="显式指定载体类型（缺省按扩展名推断）")
    p_hide.set_defaults(func=cmd_hide)

    p_extract = sub.add_parser("extract", help="从二进制载体提取隐写内容")
    p_extract.add_argument("-i", "--input", required=True, help="载体文件路径")
    p_extract.add_argument("-o", "--output", help="输出文件路径（缺省输出到标准输出）")
    p_extract.add_argument("-p", "--password", help="解密口令")
    p_extract.add_argument("--type", choices=SUPPORTED_BINARY_TYPES,
                           help="显式指定载体类型")
    p_extract.set_defaults(func=cmd_extract)

    p_cap = sub.add_parser("capacity", help="评估载体容量")
    p_cap.add_argument("-i", "--input", required=True, help="载体文件路径")
    p_cap.add_argument("--type", choices=SUPPORTED_BINARY_TYPES)
    p_cap.add_argument("--encrypted", action="store_true", help="按加密帧计算负载上限")
    p_cap.set_defaults(func=cmd_capacity)

    p_th = sub.add_parser("text-hide", help="零宽字符文本隐写")
    cover_group = p_th.add_mutually_exclusive_group()
    cover_group.add_argument("--cover-file", help="封面文本文件")
    cover_group.add_argument("--cover", help="封面文本字符串")
    secret_tg = p_th.add_mutually_exclusive_group()
    secret_tg.add_argument("-s", "--secret-file", help="待隐藏内容文件")
    secret_tg.add_argument("--secret", help="待隐藏文本字符串")
    p_th.add_argument("-o", "--output", help="输出文件路径")
    p_th.add_argument("-p", "--password", help="加密口令")
    p_th.add_argument("--position", choices=("end", "start", "split"),
                      default="end", help="隐写块插入位置，默认文末")
    p_th.set_defaults(func=cmd_text_hide)

    p_te = sub.add_parser("text-extract", help="提取零宽字符隐写内容")
    input_group = p_te.add_mutually_exclusive_group()
    input_group.add_argument("-i", "--input", help="含隐写内容的文本文件")
    input_group.add_argument("--text", help="直接传入含隐写内容的字符串")
    p_te.add_argument("-o", "--output", help="输出文件路径")
    p_te.add_argument("-p", "--password", help="解密口令")
    p_te.add_argument("--as-text", action="store_true", help="把负载按 UTF-8 文本输出")
    p_te.set_defaults(func=cmd_text_extract)

    p_ts = sub.add_parser("text-strip", help="清除文本中的零宽隐写符号")
    strip_group = p_ts.add_mutually_exclusive_group()
    strip_group.add_argument("-i", "--input", help="文本文件")
    strip_group.add_argument("--text", help="文本字符串")
    p_ts.add_argument("-o", "--output", help="输出文件路径")
    p_ts.set_defaults(func=cmd_text_strip)

    p_ver = sub.add_parser("version", help="输出版本号")
    p_ver.set_defaults(func=cmd_version)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except VeilKitError as exc:
        if args.debug:
            raise
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    except (BrokenPipeError, KeyboardInterrupt):
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
