param(
    [string]$OpenScad = $env:OPENSCAD_EXE,
    [string]$PythonExe = 'python',
    [string]$DependencyPath = '',
    [string]$OutputDirectory = "$PSScriptRoot/exports"
)
# 从脚本自身推导项目工具路径，调用者可在任意工作目录运行。
$ErrorActionPreference = 'Stop'
# 依赖目录仅在当前会话生效，不会写入用户或机器的全局变量。
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
if (-not $DependencyPath) { $DependencyPath = Join-Path $projectRoot 'tools/cad-python' }
# 显式参数与环境变量优先，便携目录其次，最后查询PATH。
if (-not $OpenScad) {
    $localTool = Join-Path $projectRoot 'tools/openscad/openscad.com'
    if (Test-Path -LiteralPath $localTool) { $OpenScad = $localTool }
    else { $OpenScad = (Get-Command openscad.com, openscad -ErrorAction SilentlyContinue | Select-Object -First 1).Source }
}
# 不下载依赖、不修改全局环境，也不自动打开GUI。
if (-not $OpenScad) { throw '找不到OpenSCAD，请用-OpenScad传入官方工具路径。' }
$env:PYTHONPATH = $DependencyPath
Write-Output "OpenSCAD: $OpenScad"
Write-Output "Python dependency path: $DependencyPath"
# 失败直接上抛，调用方不会把历史PNG或STL当作本次成功证据。
# 导出、实际网格检查、见证与图像生成在一个入口闭环。
& $PythonExe (Join-Path $PSScriptRoot 'build.py') --openscad $OpenScad --output $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "主底板导出验证失败：$LASTEXITCODE" }
