#!/usr/bin/env bash
# VeilKit Linux/macOS 一键构建脚本：测试 -> wheel -> 输出产物清单
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/3] 运行单元测试"
PYTHONPATH=src python3 -m unittest discover -s tests

echo "==> [2/3] 构建 wheel"
python3 -m pip wheel . --no-deps -w dist

echo "==> [3/3] 产物清单"
ls -lh dist
echo "构建完成，可执行: pip3 install dist/veilkit-*.whl"
