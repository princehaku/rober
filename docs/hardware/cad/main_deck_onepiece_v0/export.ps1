param(
 [string]$OpenScad=$env:OPENSCAD_EXE,
 [string]$PythonExe='python',
 [string]$OutputDirectory="$PSScriptRoot/exports"
)
# 从脚本自身定位项目，允许从系统临时目录等任意cwd调用。
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
# 显式参数/环境变量优先，不下载工具，不改全局环境。
if (-not $OpenScad) { $OpenScad=Join-Path $projectRoot 'tools/openscad/openscad.com' }
$env:PYTHONPATH=Join-Path $projectRoot 'tools/cad-python'
# 入口只导出这一件，不重复跑旧榫卯/ROS测试。
& $PythonExe -B (Join-Path $PSScriptRoot 'export.py') --openscad $OpenScad --output $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "一体底座导出失败：$LASTEXITCODE" }
