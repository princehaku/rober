# 地面后卸翻斗 v0

给你继续改的参数化机械布局草稿。打开 `ground_dump.scad` 即可编辑；`exports/overview.png` 对照运输 0° 与后卸 55°。垃圾目标质量 2 kg，图中斗体、骨架、丝杆、传感器尺寸和孔位均为设计占位。本轮交付范围为 CAD 几何及候选打印件，尚未完成载重、推力、刚度或防倾覆验证。

## 布局与材料分工

- 坐标：X 正方向为车头，X 负方向为后卸方向；Y 为左右，Z 向上；模型尺寸单位按 mm 设计。
- 灰色：拟用金属的纵梁、横梁、后铰轴、斗底横向支点、前端双立柱和连接简化底盘的四个支脚。支脚孔位与安装面承力能力仍待实测。蓝色：低位垃圾斗占位。橙色：三类打印适配件。紫色：单根中央丝杆/电动推杆占位。红色：雷达包络；深色小盒：相机包络。
- 固定前架：雷达顶置，相机在下方独立 L 形座上朝前下倾；相机座带两侧加强筋。雷达板落在两立柱顶部，相机底板落在金属横梁上，底座适配板夹在立柱脚与金属导轨之间。
- 后铰轴固定，斗底前端抬起。单根执行器两端跟随车架下铰点与斗底上铰点连线，图形用伸缩杆表达丝杆驱动意图；实际丝杆、导向、螺母、摆动自由度、制动与耳板尚待选型设计。
- 斗顶、后侧斜口保持开放，后口只留 12 mm 低挡边。后铰轴设计位置 X=-120 mm，向简化底盘后方外伸，便于表达地面落料路径。低挡边只能提供初步限位，运输掉落、垃圾袋挂边、真实摩擦和卸料干净程度均待试验；后移也会增加重心风险。
- 橙色底座属于传感器架适配件；垃圾与执行器载荷应经金属骨架闭合。底座的主骨架固定方式、真实螺栓头/垫片工具空间、铰链间隙和止挡均待实物细化。

## 打开和修改

1. 本机便携版已放在项目目录：双击 `E:\rober\tools\openscad\openscad.exe`，再用“文件 → 打开”选择 `E:\rober\docs\hardware\cad\ground_dump_v0\ground_dump.scad`。本轮使用 OpenSCAD 2021.01，未修改全局环境；换电脑可从 [OpenSCAD 官方下载页](https://openscad.org/downloads.html) 获取便携版，完整解压到仓库的 `tools/openscad/`。
2. 在右侧 Customizer 展开参数组；若未显示，通过“视图 → 隐藏 Customizer”切换显示。也可直接修改源文件顶部参数。所有参数后面的数值范围只是编辑辅助。
3. `part=assembly` 看整体；`dump_angle=0` 看运输，`55` 看后卸。F5 快速预览，F6 完整布尔运算。透视颜色用于装配辨认，导出的 STL 不带颜色。
4. 将 `part` 改为 `lidar_plate`、`camera_bracket` 或 `base_adapter`，F6 后通过“文件 → 导出 → STL”导出单个候选件。单件底面均为 Z=0。
5. 修改尺寸后先检查孔槽到边缘的余量、柱脚/孔位接触、斗体整个转角范围与传感器和线缆的间隙。源文件内有部分几何约束，触发断言时须调整耦合参数；断言通过仍需人工装配复核。

| 参数 | 默认值 mm / ° | 用途与测量动作 |
|---|---:|---|
| `dump_angle` | 0 | 运输/后卸；预览给出 55°，真实卸净角待试验 |
| `bucket_length/width/height` | 180 / 132 / 90 | 斗外尺寸，按垃圾袋体积和底盘能力重定 |
| `bucket_wall/rear_lip_height` | 3 / 12 | 斗体占位壁厚/后口低挡边，未定材料工艺 |
| `hinge_x/hinge_z` | -120 / 150 | 相对简化底盘原点的后铰轴位置，重做落料/重心检查 |
| `mast_x/mast_spacing/mast_size` | 110 / 90 / 12 | 前架位置/左右中心距/金属柱方形外包络 |
| `lidar_height/camera_height` | 310 / 222 | 雷达板底面/相机座底面高度 |
| `lidar_plate_depth/margin/thickness` | 70 / 20 / 5 | 雷达板 X 深度、相对柱距的 Y 总余量、厚度 |
| `lidar_hole_spacing_x/y` | 35 / 35 | 雷达设备四孔中心距，须量实物 |
| `lidar_hole_diameter/slot_travel` | 3.4 / 6 | 雷达四孔槽宽/直线移动量 |
| `camera_width/base_depth/plate_height/thickness` | 64 / 42 / 40 / 5 | 相机座 Y 宽、X 底深、前板高度、厚度 |
| `camera_pitch/hole_spacing/hole_diameter` | 10° / 28 / 3.4 | 相机下倾/前板两孔中心距/孔径 |
| `base_length/width/thickness` | 140 / 120 / 6 | 底座适配板外形 |
| `base_hole_spacing_x/y` | 90 / 80 | 底盘固定槽中心距，须量实物；无厂家兼容承诺 |
| `base_hole_diameter/slot_travel` | 4.5 / 12 | 底座固定槽宽/移动量 |
| `show_chassis/show_bucket/show_sensor_envelopes/show_actuator/show_ground` | true | 独立隐藏参考外形、斗体、传感器、执行器、地面 |

`lidar_plate_width` 自动等于柱距加余量；柱脚、雷达立柱孔、相机横梁随主参数联动。螺钉、螺母、垫片、线缆和实际传感器固定壳体未建模。不要将设备包络圆柱外径当作实物尺寸。

## 候选打印件与试装顺序

| STL | 默认包络 | 建议摆放和注意事项 |
|---|---|---|
| `exports/lidar_plate.stl` | 70 × 110 × 5 | 平底向下，无悬空桥接；试印孔槽校准片后再印整板 |
| `exports/camera_bracket.stl` | 约 48.87 × 64 × 43.39 | 平底向下，前板朝外倾 10°，两侧有筋；切片时检查外倾面/孔桥接是否需局部支撑 |
| `exports/base_adapter.stl` | 140 × 120 × 6 | 平底向下，先验证立柱及底盘孔槽，禁止用打印板独立承托垃圾载荷 |

建议先量雷达、相机和车架孔位与设备外包络，改单件参数 → 切片查看孔和壁 → 小件试印 → 空载手拧试装 → 断电手动走完整翻斗行程 → 保持无人/无障碍的后方落料区，逐级增加假载荷并测总质量和重心。材料、打印方向、层间强度和螺栓预紧需自行核算，本稿未批准材料选型。

## 一键重导出与轻量验证

在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs/hardware/cad/ground_dump_v0/export.ps1
```

脚本可从任意工作目录运行，源文件、默认工具与依赖均从脚本位置推导。OpenSCAD 选择顺序为显式 `-OpenScad`、`OPENSCAD_EXE`、项目 `tools/openscad/openscad.com`、PATH。Python 依赖默认在本机项目 `E:\rober\tools\cad-python\`，允许 `-DependencyPath` 覆盖；Python 解释器用 `-PythonExe` 指定。换电脑需准备 numpy、trimesh、Pillow，例如在仓库根目录执行：

```powershell
python -m pip install --target ./tools/cad-python numpy trimesh Pillow
```

`tools/openscad/` 与 `tools/cad-python/` 已精准加入 `.gitignore`，仅保留本机第三方工具，Git 中保存设计文件与导出入口。脚本不自动下载依赖，不改全局 PATH。`export.ps1` 保留 UTF-8 BOM 以兼容 Windows PowerShell 5 的中文解析。导出入口优先采用数值 `part_id=1/2/3`，预览用 `part_id=4` 强制选择装配，避免 Windows 原生命令的字符串引号差异与 GUI 保存值影响批量导出；日常 GUI 保持隐藏的 `part_id=0`，继续使用 `part` 下拉菜单。

输出包括 3 个 STL、2 个固定柱距 90/100 的对照检查 STL、两张装配 PNG、隐藏斗体的 `mechanism_55.png` 机构检查图、概览 PNG 和 `geometry_report.json`。检查返回码、非空、封闭、法线一致、单连通、正体积与底面落零；固定对照组把柱距 90 改成 100 后板宽须增大 10 mm（原始余量参数下为 110 至 120）。用户修改源文件默认柱距不影响该对照检查，实际打印件始终用当前源文件参数导出。报告不包含装配碰撞、有限元、打印质量、物理载重或传感器视野验证。对照 STL 用于验证参数化，实际打印请使用确认过尺寸的单件。

## 资料来源与证据边界

- `docs/vendor/VENDOR_INDEX.md`：本项目硬件资料入口。
- `docs/vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl`：二进制 STL 共 546006 三角面，原坐标包围框 `[-86.1494,-91.5537,-35.7864]` 至 `[86.2494,102.4765,64.1528]`，轴向尺寸约 `172.3988 × 194.0302 × 99.9392`。**STL 自身不声明单位**；本稿将其当作毫米量级参考，长轴作为车长是设计假设。图中底盘采用简化盒体与轮子，并未导入原网格，不能用简化底盘测孔位或做严谨干涉检查。
- `docs/vendor/waveshare_wave_rover/WAVE ROVER-EP PDF.pdf` 和 `WAVE ROVER-EP DXF.dxf`：已读文件信息与图纸入口；PDF 一页提取文本无尺寸标注，DXF 本轮仅核对元数据，未从图中估算安装尺寸，也未采用其中孔距。
- `docs/vendor/lidar_pkg_ros2-main/models/lidar_mount.stl`、`urdf/lidar.urdf`：已查看参考包络。STL 原始包围尺寸约 `0.08 × 0.02953 × 0.14`，与底盘 STL 存在数量级差异，单位未核实，故未复用它的尺寸或孔位。URDF 中传感器图形也只作为示意。
- [OpenSCAD 官方下载](https://openscad.org/downloads.html)与官方站点链接的[用户手册：命令行](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Using_OpenSCAD_in_a_command_line_environment)：便携工具和导出参数入口。

底盘额定载荷未得到本地资料确认；2 kg 仅指垃圾目标，总载荷还包括斗、架、执行器、电池及电子件。丝杆推力和两端距离随翻转变化，运输状态接近低夹角，所需推力可能较大；需要实际机构计算、全行程防卡死、机械止挡、防夹、断电锁定和满载防倾覆评估。雷达扫描平面、相机视野、天线/散热/维修空间及线缆弯曲也需实物检查。本轮不修改 OKR 完成度。
