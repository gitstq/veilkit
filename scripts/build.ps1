# VeilKit Windows 一键构建脚本（PowerShell）
# 用法：在项目根目录执行  powershell -ExecutionPolicy Bypass -File scripts\build.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> [1/3] 运行单元测试" -ForegroundColor Cyan
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw "单元测试未通过，已终止构建" }

Write-Host "==> [2/3] 构建 wheel" -ForegroundColor Cyan
python -m pip wheel . --no-deps -w dist
if ($LASTEXITCODE -ne 0) { throw "wheel 构建失败" }

Write-Host "==> [3/3] 产物清单" -ForegroundColor Cyan
Get-ChildItem dist | Format-Table Name, Length

Write-Host "构建完成，可执行: pip install dist\veilkit-*.whl" -ForegroundColor Green
