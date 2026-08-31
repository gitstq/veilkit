# VeilKit 跨平台任务入口（Linux / macOS）
# Windows 用户可直接运行 scripts\build.ps1，或逐条复制其中命令。

PYTHON ?= python3
SRC := src

.PHONY: help test wheel sdist build install clean demo

help: ## 显示全部可用目标
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

test: ## 运行全部单元测试（零第三方依赖）
	PYTHONPATH=$(SRC) $(PYTHON) -m unittest discover -s tests -v

wheel: ## 构建 wheel 到 dist/
	$(PYTHON) -m pip wheel . --no-deps -w dist

sdist: ## 构建源码分发包到 dist/
	$(PYTHON) -m pip install --quiet build && $(PYTHON) -m build --sdist

build: wheel ## 一键构建（默认 wheel）

install: ## 安装到当前环境
	$(PYTHON) -m pip install .

clean: ## 清理构建产物与缓存
	rm -rf build dist *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

demo: ## 快速演示（需先准备载体，详见 examples/）
	PYTHONPATH=$(SRC) $(PYTHON) -m veilkit version
