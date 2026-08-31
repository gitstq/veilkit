# 贡献指南（Contributing to VeilKit）

感谢你对 VeilKit 的兴趣！欢迎以 Issue、Pull Request、文档改进等方式参与贡献。

## 开发环境

VeilKit 运行时**零第三方依赖**，仅需 Python ≥ 3.9：

```bash
git clone https://github.com/gitstq/veilkit.git
cd veilkit
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## 提交前检查

```bash
make test                 # Linux/macOS：运行全部 32 项测试
# 或不使用 Make：
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

所有测试必须通过；新增载体/密码学逻辑时，请同步补充：

1. **往返测试**（hide → extract 等价）；
2. **异常路径测试**（损坏文件、容量不足、错口令、篡改）；
3. 涉及密码学时，优先补充**公开标准测试向量**（如 RFC 向量）。

## 代码规范

- 遵循 PEP 8，行宽建议 ≤ 100；
- 公共函数/类必须有中文或英文 docstring，说明参数、异常与线程安全性；
- 不允许引入运行时第三方依赖（标准库能力不足时请先开 Issue 讨论）；
- 错误必须通过 `veilkit.errors` 中的异常类型表达，禁止静默吞错。

## Pull Request 流程

1. Fork 仓库并从 `main` 切出特性分支：`feat/xxx`、`fix/xxx`、`docs/xxx`；
2. 提交信息遵循 **Angular Conventional Commits**：
   - `feat: 新增 xxx 载体`
   - `fix: 修复 xxx 边界问题`
   - `docs: 完善 xxx 文档`
   - `refactor: 重构 xxx 模块`
   - `test: 补充 xxx 测试`
3. 在 PR 描述中说明动机、实现方式、测试方式与兼容性影响；
4. 等待 CI/维护者评审，按需修改。

## Issue 反馈

- Bug：请附上操作系统、Python 版本、复现命令、载体格式（RGB/RGBA、位深等）与报错全文；
- 功能建议：说明使用场景、期望行为与备选方案。

## 安全问题

请勿在公开 Issue 中提交安全漏洞细节，可通过仓库 Security 面板或私下联系维护者披露。

## 合规提醒

VeilKit 仅用于隐私保护、数字水印、CTF 教学、无损取证演练等合法场景；
请勿将其用于规避法律义务、侵犯他人权益或违反所在司法辖区法律的用途。
