# 地面卸料机器人支架设计初稿

sprint_type: micro

状态：已完成 CAD 草案验证，独立规格/质量复核通过当前草案范围，进入 Git 交付；后续实物修改与试装待用户推进。单一硬件 owner。用户明确要求“ok 你先设计 我来改”，本轮范围为设计参考，不接入硬件、不实现自动卸料控制、不变更 OKR 百分比。

## 最小实施计划

- 需求：以 2 kg 垃圾为目标，运输时低位居中，丝杆驱动翻斗向后卸至地面；前端车架固定雷达和相机，相机不独占整层板。
- owner：robot-hardware-engineer；主节点只派单、读取结果、验收和留档。
- 产物范围：`docs/hardware/cad/ground_dump_v0/` 下的参数化 CAD 源文件、中文修改说明、导出入口、打印候选件 STL、装配预览，以及本文件。
- 所有尚未实测的设备外形、孔距、厚度、高度、翻斗和丝杆尺寸均明确为设计占位参数；现有 vendor 图纸仅提供安装参考，未经实测不得称为兼容。
- 打印候选件限传感器支架；翻斗、转轴、主骨架、丝杆为装配占位，标注金属承力及待选型，不宣称其可承载 2 kg。
- 顺序：读取 vendor → 检查可用 CAD 工具 → 建立参数化模型 → 导出 STL/运输与卸料预览 → 校验几何及修改后的参数 → 同步说明和证据。
- 验收命令：硬件 owner 提供并运行可重复的导出命令；逐件检查导出返回码、非空封闭网格及尺寸；核查默认和修改参数的导出；检查运输/卸料预览；`git diff --check`。
- 无 ROS2、串口或驱动改动，无需运行 ROS2 构建。

## 实际改动

- `docs/hardware/cad/ground_dump_v0/ground_dump.scad`：唯一参数化 CAD 源文件，Customizer 提供斗体、后铰轴、转角、传感器孔槽、高度、金属柱和底座参数。低位斗向后翻，斜口配 12 mm 低挡边；后铰轴占位 X=-120 mm，给后落料留出外伸。前端固定金属双柱顶雷达、下相机；四个占位金属脚连接简化底盘与纵梁。单根中央执行器跟随上下铰点连线，相机座带两侧加强筋。
- `README.md`：中文参数表、修改/F5/F6/导出步骤、三类打印件试装顺序、颜色方向、资料来源、设计假设与载重/机构边界。
- `export.ps1`：Windows 可重复入口，支持自选 OpenSCAD/Python 路径；导出前清理同名目标，逐步检查返回码。数字零件入口优先，批量输出不受 GUI 保存的单件选择影响。
- `validate.py`：轻量网格检查及双状态 PNG 排版，检查默认打印件和独立固定 90/100 mm 柱距对照；不自动修网格，不修改机械几何。
- `exports/`：`lidar_plate.stl`、`camera_bracket.stl`、`base_adapter.stl` 三个打印候选；`lidar_plate_reference_check.stl`、`lidar_plate_wide_check.stl` 两个参数回归件；`transport.png`、`dump_55.png`、`mechanism_55.png`（隐藏斗体以看中央执行器）、`overview.png`；`geometry_report.json`。
- 技术中文注释占文件总行数：SCAD 58/256=22.7%，PowerShell 16/65=24.6%，Python 18/80=22.5%。未修改 vendor、OKR、既有 sprint、ROS2 代码或硬件配置；主节点验收后授权仅将本 CAD 目录和本 sprint 文件纳入常规提交/推送，不进行 PR、合并或部署。

## 验证结果

初始验证环境：Windows 本机；Python 3.13.12、OpenSCAD 2021.01、trimesh 5.2.0、numpy 2.5.4，Pillow 使用本机已有版本。首次验证时工具位于 `%LOCALAPPDATA%/rober-cad-tools/`，后按用户要求迁入项目 `tools/`，具体事实见末节；未改全局 PATH，无 ROS2 构建。

已读来源：`docs/vendor/VENDOR_INDEX.md`；WAVE ROVER 扩展平台 PDF/DXF 文件；`WAVE ROVER_MODEL_STL.stl`；雷达 `models/lidar_mount.stl` 与 `urdf/lidar.urdf`。底盘 STL 546006 面，原始包围尺寸 172.3988×194.0302×99.9392，单位未声明；仅作为毫米量级及长轴朝前的设计假设。扩展平台 PDF 提取文本无尺寸标注，DXF 未采用孔距。雷达 mount 原始尺寸 0.08×0.02953×0.14，单位与适配未确认，故未复用。实际安装孔位全部待测。

实际运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs/hardware/cad/ground_dump_v0/export.ps1
git diff --check
```

最终导出链返回码 **0**；五个 STL、三张直接 CAD PNG 均为 `EXPORT OK`。网格检查摘要如下，全部非空、封闭、法线一致、单连通、正体积、最低点 Z=0。

| STL | 三角面 | 包围尺寸 mm | 体积 mm³ |
|---|---:|---|---:|
| lidar_plate | 1432 | 70×110×5 | 37141.735 |
| camera_bracket | 1012 | 48.870×64×43.392 | 27591.447 |
| base_adapter | 1220 | 140×120×6 | 98933.079 |
| lidar_plate_reference_check（柱距90） | 1432 | 70×110×5 | 37141.735 |
| lidar_plate_wide_check（柱距100） | 1432 | 70×120×5 | 40641.735 |

参数回归输出：`PASS parameter change: plate width 110.0 -> 120.0 mm`。用 `view_image` 逐张查看默认运输、55° 卸料、隐藏斗体的机构图及概览：后口开放、传感器固定、相机加强筋、中央执行器上下支点和四个车架脚可辨；这是视觉布局证据，未运行碰撞或载荷仿真。

额外可修改性回归：把三份源码/脚本复制至 `%LOCALAPPDATA%/rober-cad-tools/modified-source-check-20261101/`，仅在副本中将源文件 `part="assembly"` 改为 `part="lidar_plate"`、`mast_spacing=90` 改为 `95`，运行副本的完整 `export.ps1`。返回码 **0**；用户打印件雷达板实际变为 70×115×5、体积38891.735；相机仍为48.870×64×43.392，底座仍为140×120×6；固定90/100对照继续通过。`view_image` 查看副本概览仍为两张整机状态，保存单件选择没有污染预览。仓库原始参数保持不变。

`git diff --check` 返回0，无空白错误。因产物当前为未跟踪新增文件，另由 owner 执行逐文本行尾空白核对；最终 Git staged 检查由交付阶段完成。

### 失败定位与修复

1. 首次 Windows PowerShell 5 解析中文脚本报语法错误：UTF-8 无 BOM 被按本地编码读取。修复为 UTF-8 BOM，重新运行成功。
2. 原生命令传 `part="lidar_plate"` 时引号被 Windows PowerShell 剥离，OpenSCAD 将其解释为变量并生成空对象。改用数值 `part_id`，并让非零数字选择优先、PNG 显式选择装配。
3. 主节点/独立 review 发现参数检查依赖用户默认柱距、GUI 保存单件会污染批量输出。改为独立90/100对照、数字入口优先；通过同时修改默认柱距95和单件选择的完整回归。
4. 视觉审查补齐四个金属连接脚；执行器改成用户要求的一根中央占位并补下铰点横梁；相机座增加两侧筋；后铰轴后移，避免初稿卸料口紧贴简化底盘后缘。全部重新导出并检查。

独立复核结论：用户改默认柱距影响导出检查、GUI 保存单件选择污染批量输出的两项问题均已解决；四个连接脚已补齐。主节点确认独立规格/质量复核通过本轮 CAD 草案范围。该结论仅覆盖软件导出可修改性、网格与布局示意，实物安全验证范围保持原边界。

## 剩余风险

- 本地资料未确认底盘额定载重；总载荷需包含垃圾、斗体、骨架、丝杆和电子件。
- 仍需实测安装孔位、设备外形、雷达扫描面、垃圾体积、执行器规格、满载重心与翻斗运动范围。
- 本轮不提供承载、倾覆、丝杆推力、传感器视野、打印装配或上车验证结论。
- 运输低挡边仅为初稿限位，垃圾袋颠簸掉落/挂边、地面卸净与后车轮/真实底盘净空仍待实测。中央丝杆运输夹角低，推力可能较大，需机构计算；未给出可购买型号、行程、锁止或控制策略。
- 四个车架脚、主梁、轴与斗体连接目前只表达连续布局，真实孔位、承力点、紧固工具空间、机械止挡、防夹、线缆与散热维修空间均未定型。
- 交付范围仅可编辑 CAD、STL 几何及 PNG 布局；下一步由用户量车/传感器并修改，小件试印后进行空载全行程、逐级假载荷及满载重心检查。无 HIL 或 OKR 完成度增量。
- 最近两轮目录核查：2026.09.17 性能迭代已完成软件范围；2026.06.12 未发现 final.md。本设计任务不重复消费其运行环境或导航 blocker。

## 用户要求的工具路径迁移

- 用户明确要求把工具放到项目内。迁移前确认没有 OpenSCAD 进程，未终止用户进程；在同一 PowerShell 会话逐一核实解析后的精确源路径和目标路径、目标无冲突，再复制并逐文件校验 SHA256，最后仅删除校验通过的两个旧工具目录。
- 完整便携目录现为 `E:\rober\tools\openscad\`，182 个文件全部哈希一致；GUI 为 `tools/openscad/openscad.exe`，CLI 为 `tools/openscad/openscad.com`，`--version` 输出 `OpenSCAD version 2021.01`。
- 本任务 Python 依赖现为 `E:\rober\tools\cad-python\`，1742 个文件全部哈希一致；原 `openscad-2021.01` 和 `python` 目录均已迁走。父缓存内下载 ZIP、历史回归目录保持原位。
- 实际修改仅 `.gitignore`、`export.ps1`、`README.md` 和本 sprint 文件。导出脚本优先显式参数/环境变量，其后从脚本位置找项目 OpenSCAD，最后查询 PATH；默认 Python 依赖也从脚本位置推导到项目目录。保留 UTF-8 BOM，中文技术注释为 19/75 行，超过20%。README 给出项目内双击 exe 与打开现有模型的路径。
- `.gitignore` 精准忽略 `/tools/openscad/` 和 `/tools/cad-python/`；原文件统一为 LF 以通过行尾空白检查，原忽略规则保持相同。第三方工具和库不进入 Git，模型源文件及已有导出产物保持不变。

验证命令摘要：新路径 `openscad.com --version` 返回0；本次验证进程清空 `OPENSCAD_EXE` 后切到系统临时目录，以绝对路径运行 `E:\rober\docs\hardware\cad\ground_dump_v0\export.ps1 -OutputDirectory "$env:TEMP/rober-project-cad-migration-check-20261101"`，完整返回0。日志明确输出 `OpenSCAD: E:\rober\tools\openscad\openscad.com` 和 `Python dependency path: E:\rober\tools\cad-python`；五个 STL 均封闭、单连通、正体积，参数回归110→120 mm通过，三张CAD PNG及概览生成成功。额外核对 numpy/trimesh 的 `__file__` 均在项目 `tools/cad-python/`。

`git check-ignore` 两个工具目录、exe/com 和 numpy 关键文件均命中；`git diff --check` 通过。首次追加 `.gitignore` 时遇到既有 CRLF 与新增行导致的空白检查失败，统一 LF 后通过。交付仅暂存上述四个文本文件，再运行暂存区空白检查和名单审查；正常提交/推送，不改远端历史。

本轮剩余边界：第三方工具仅在当前本机项目目录，换电脑需另备便携版和 Python 依赖；Python 解释器与原有 Pillow 继续使用本机环境。机械载荷、机构与实物验证风险沿用上节，本次路径迁移没有新增硬件结论。
