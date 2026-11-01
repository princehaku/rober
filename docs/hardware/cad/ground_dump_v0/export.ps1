param(
    [string]$OpenScad = $env:OPENSCAD_EXE,
    [string]$PythonExe = 'python',
    [string]$DependencyPath = '',
    [string]$OutputDirectory = "$PSScriptRoot/exports"
)
# 项目工具目录便于用户直接找到，脚本不会下载软件或修改全局环境。
$ErrorActionPreference = 'Stop'
# 从脚本位置推导仓库根目录，换工作目录也能找到本地工具和依赖。
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
if (-not $DependencyPath) { $DependencyPath = Join-Path $projectRoot 'tools/cad-python' }
if (-not $OpenScad) {
    $projectOpenScad = Join-Path $projectRoot 'tools/openscad/openscad.com'
    # 显式参数及环境变量优先，其后使用项目便携版，最后查询 PATH。
    if (Test-Path -LiteralPath $projectOpenScad) { $OpenScad = $projectOpenScad }
    else {
        $found = Get-Command openscad.com, openscad -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $OpenScad = $found.Source }
    }
}
# 显式路径和 PATH 均可用，缺失时给用户可操作的提示。
if (-not $OpenScad -or -not (Get-Command $OpenScad -ErrorAction SilentlyContinue)) {
    throw '找不到 OpenSCAD。请安装官方便携版并用 -OpenScad 传入 openscad.com 路径。'
}
$source = Join-Path $PSScriptRoot 'ground_dump.scad'
# 路径均从脚本自身目录解析，调用者可以在任意工作目录运行。
New-Item -ItemType Directory -Force $OutputDirectory | Out-Null
# 输出实际选择路径，便于核对跨目录运行时采用的工具来源。
Write-Output "OpenSCAD: $OpenScad"
Write-Output "Python dependency path: $DependencyPath"
& $OpenScad --version
# 每次导出都检查返回码和文件长度，避免上次的产物掩盖失败。
function Export-Cad([string]$Name, [string[]]$Options) {
    $target = Join-Path $OutputDirectory $Name
    # 仅移除本次同名导出文件，避免历史文件让非空检查误通过。
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target }
    $cadArgs = @('-o', $target) + $Options + @($source)
    # 参数数组直接交给原生程序，避免拼接成第二层 shell 命令。
    & $OpenScad @cadArgs
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD 导出失败：$Name，返回码 $LASTEXITCODE" }
    if (-not (Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -eq 0) {
        throw "导出文件为空：$Name"
    }
    Write-Output "EXPORT OK $Name"
}
# 三种候选打印件分别导出，不把装配里的多个实体当作单个打印件。
$partId = 0
# 数字入口与源文件一一对应，跨 PowerShell 版本不用转义 CAD 字符串。
foreach ($partName in @('lidar_plate', 'camera_bracket', 'base_adapter')) {
    $partId++
    Export-Cad "$partName.stl" @('--export-format','binstl','-D',"part_id=$partId")
}
# 参数扰动直接重用源文件；宽度增加 10 毫米应反映在输出包围尺寸。
Export-Cad 'lidar_plate_reference_check.stl' @('--export-format','binstl','-D','part_id=1','-D','mast_spacing=90')
Export-Cad 'lidar_plate_wide_check.stl' @('--export-format','binstl','-D','part_id=1','-D','mast_spacing=100')
# 四孔样板与实际金属框架分别导出，后者只供切片测量，不属于打印候选。
Export-Cad 'mount_template.stl' @('--export-format','binstl','-D','part_id=5')
foreach ($kind in @('reference','changed')) {
    $pitchX = 58
    $pitchY = 86
    if ($kind -eq 'changed') { $pitchX = 68; $pitchY = 96 }
    # 固定对照组不依赖用户默认孔距，孔距变化应同时驱动样板和实际四柱。
    $mountArgs = @('--export-format','binstl','-D',"mount_pitch_x=$pitchX",'-D',"mount_pitch_y=$pitchY",'-D','mount_clearance=3','-D','thread_diameter=2.5','-D','driver_clearance_diameter=10')
    Export-Cad "mount_template_${kind}_check.stl" ($mountArgs + @('-D','part_id=5'))
    Export-Cad "mount_frame_${kind}_check.stl" ($mountArgs + @('-D','part_id=7'))
    # 使用与装配完全相同的前适配板，防止打印件覆盖螺栓头而预览未察觉。
    Export-Cad "sensor_adapter_${kind}_check.stl" ($mountArgs + @('-D','part_id=8'))
}
# 显式选择装配入口，用户保存的 GUI 单件选择不会影响状态预览。
$view = @('-D','part_id=4','--imgsize','1400,1050','--projection','o','--camera','-420,-600,390,0,0,160','--viewall','--preview','--colorscheme','Tomorrow')
# 同一机位便于对照运输与卸料，颜色保留零件职责区分。
Export-Cad 'transport.png' ($view + @('-D','dump_angle=0'))
Export-Cad 'dump_55.png' ($view + @('-D','dump_angle=55'))
# 中央执行器会被斗侧壁遮挡，单独输出隐藏斗体的机构检查图。
Export-Cad 'mechanism_55.png' ($view + @('-D','dump_angle=55','-D','show_bucket=false'))
# 专门安装图移去业务部件，直接展示四柱和紧固件；俯视图用于孔位对照。
$installView = @('-D','part_id=6','--imgsize','1300,1050','--projection','o','--viewall','--preview','--colorscheme','Tomorrow')
Export-Cad 'mount_install_raw.png' ($installView + @('--camera','210,-320,250,0,0,95'))
Export-Cad 'mount_top_raw.png' ($installView + @('--camera','0,0,500,0,0,110'))
# 验证依赖默认由项目本地目录提供，也允许使用调用者指定的环境。
$previousPath = $env:PYTHONPATH
# 依赖目录临时添加到当前进程，退出时归还调用者原配置。
try {
    if (Test-Path -LiteralPath $DependencyPath) { $env:PYTHONPATH = "$DependencyPath;$previousPath" }
    & $PythonExe (Join-Path $PSScriptRoot 'validate.py') $OutputDirectory
    # Python 断言失败必须中断整条导出链，不能仅输出警告后继续。
    if ($LASTEXITCODE -ne 0) { throw "几何检查失败：返回码 $LASTEXITCODE" }
} finally {
    # 保留调用者的环境设置，便于在已有开发环境中重复运行。
    $env:PYTHONPATH = $previousPath
}
Write-Output '导出及几何检查完成。打印与机械安全仍需实物验证。'
