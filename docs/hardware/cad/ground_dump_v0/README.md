# 地面后卸翻斗 v0

给你继续改的参数化机械布局草稿。打开 `ground_dump.scad` 即可编辑；`exports/overview.png` 对照运输 0° 与后卸 55°，`exports/mount_installation.png` 看四孔安装。垃圾目标质量 2 kg；用户确认四孔采用 M2.5，孔距由本地 DXF 定位。斗体、骨架、丝杆、设备外形及层高仍为设计占位，尚未完成载重、推力、刚度或防倾覆验证。

## 布局与材料分工

- 坐标原点为上下板四孔组中心；X 正方向暂定为车头，X 负方向为后卸，Y 为左右，Z 向上。模型单位 mm；相机/车头与厂家图纸的前后关系仍是映射假设。
- 灰色：拟用金属的纵梁、横梁、后铰轴、斗底支点、双立柱和四根中空隔柱。青色：上层四耳参考板。金色：M2.5轴、头部和垫片占位。蓝色：垃圾斗；橙色：传感器打印适配件；紫色：中央执行器占位；红色：雷达包络。
- 固定前架：雷达顶置，相机在下方独立 L 形座上朝前下倾。传感器底座板缩短为50×120，四个底盘螺栓位于其后方；加长底座时会联动开工具窗，距边不足3 mm时开口到边缘，避免薄小筋。四根隔柱经原上层板、金属安装横梁接主纵梁，前横梁继续承托双立柱。
- 后铰轴固定，斗底前端抬起。单根执行器两端跟随车架下铰点与斗底上铰点连线，图形用伸缩杆表达丝杆驱动意图；实际丝杆、导向、螺母、摆动自由度、制动与耳板尚待选型设计。
- 斗顶、后侧斜口保持开放，后口只留 12 mm 低挡边。后铰轴设计位置 X=-120 mm，向简化底盘后方外伸，便于表达地面落料路径。低挡边只能提供初步限位，运输掉落、垃圾袋挂边、真实摩擦和卸料干净程度均待试验；后移也会增加重心风险。
- 橙色底座属于传感器架适配件；垃圾与执行器载荷应经金属骨架闭合。底座的主骨架固定方式、真实螺栓头/垫片工具空间、铰链间隙和止挡均待实物细化。

## 打开和修改

1. 本机便携版已放在项目目录：双击 `E:\rober\tools\openscad\openscad.exe`，再用“文件 → 打开”选择 `E:\rober\docs\hardware\cad\ground_dump_v0\ground_dump.scad`。本轮使用 OpenSCAD 2021.01，未修改全局环境；换电脑可从 [OpenSCAD 官方下载页](https://openscad.org/downloads.html) 获取便携版，完整解压到仓库的 `tools/openscad/`。
2. 在右侧 Customizer 展开参数组；若未显示，通过“视图 → 隐藏 Customizer”切换显示。也可直接修改源文件顶部参数。所有参数后面的数值范围只是编辑辅助。
3. `part=assembly` 看整体；`dump_angle=0` 看运输，`55` 看后卸。F5 快速预览，F6 完整布尔运算。透视颜色用于装配辨认，导出的 STL 不带颜色。
4. 将 `part` 改为 `lidar_plate`、`camera_bracket`、`base_adapter` 或 `mount_template`，F6 后通过“文件 → 导出 → STL”导出单件，底面均为 Z=0。`mount_install` 专看四柱/板/螺头安装关系。
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
| `base_length/width/thickness` | 50 / 120 / 6 | 前传感器适配板外形，减少对底盘螺头的覆盖 |
| `sensor_foot_hole_diameter` | 4.5 | 前端立柱脚孔占位，与底盘M2.5接口分开 |
| `mount_pitch_x/y` | 58 / 86 | 共用安装原点两侧的四孔中心距 |
| `thread_diameter/mount_clearance` | 2.5 / 3.0 | 用户确认螺纹 / 新金属件及样板设计通孔 |
| `upper_plate_z/thickness` | 112 / 2 | 上层参考板底面高度和板厚占位；一层顶面Z=100 |
| `mount_post_diameter/mount_ear_thickness` | 8 / 4 | 中空金属隔柱外径 / 上安装耳厚度占位 |
| `bolt_head_diameter/height` | 5 / 2 | 头部包络占位，须按采购件复核 |
| `washer_diameter/thickness/driver_clearance_diameter` | 7 / 0.8 / 10 | 垫片与工具空间占位；新板自动避让工具圆柱 |
| `mount_template_thickness` | 2.5 | 四孔对位样板厚度，禁止承重 |
| `display_direction` | 1 | ±1切换整体展示180°，不改变部件间安装方向 |
| `show_chassis/show_bucket/show_sensor_envelopes/show_actuator/show_ground` | true | 独立隐藏参考外形、斗体、传感器、执行器、地面 |

`lidar_plate_width` 自动等于柱距加余量；柱脚、相机横梁、四安装柱、金属耳和工具窗口随参数联动。新件孔距可改，原板参考孔始终保留 DXF 的58×86和原直径，改参时须确认与真实硬件重新匹配。紧固件只画包络，未建螺纹、螺钉长度或下层螺纹啮合。不要将设备包络当作实物尺寸。

斗体及前架的 `hinge_x`、`mast_x` 保留车体局部坐标；装配统一加 `body_offset_x=-22.641541`，换算到四孔组原点。`mount_pitch_x/y` 与新金属安装接口直接使用共用安装坐标，Z高度共用。

## 四孔来源、偏置与安装

用户先说“M6”，随后确认“你说的对 是2.5mm的”，当前接口采用M2.5。`mount_reference.json` 保存实体句柄、原始OCS/WCS、法向、单位和块信息；`mount_dxf_reference.png` 是实际DXF曲线重画，两图统一方向后可逐孔对应，用户原图未放进Git。

| 参考 | 四孔WCS圆心组合 mm | 原图孔径 / 中心距 |
|---|---|---|
| 上层 `WAVE ROVER-EP DXF.dxf` | X=101.837759或159.837759，Y=177.264173或263.264173 | Ø2.60；58×86 |
| 下层 `WAVE ROVER DXF.dxf` | X=249.645451或335.645451，Y=437.694635或495.694635 | Ø2.05；86×58 |

两文件 `$INSUNITS=4`（mm）、`$MEASUREMENT=1`；主体直接在modelspace，INSERT仅图框/标题栏，缩放均1。圆实体法向为(0,0,-1)，原始OCS的X为负，转WCS后翻正。上层孔组中心(130.837759,220.264173)，下层中心(292.645451,466.694635)。映射为：上层 `X=u−130.837759,Y=v−220.264173`；下层 `X=V−466.694635,Y=−(U−292.645451)`。这次90°映射使四轴落在 `X=±29,Y=±43`。

下层顶板边界基准采用实体2EA6/2EA7/2EA8/2EAB/2EAC，包围框中心(292.645451,444.053094)，孔组相对顶板中心偏22.641541 mm；上层顶视轮廓区域包围中心(109.5503445,220.264173)，相对孔组偏−21.2874145 mm。模型没有擅自把两板外形中心重合。上层和下层外形均作简化，精确曲线请看DXF重画；板厚、层高和安装耳的承力能力未实测。

M2.5来自用户现有安装；下层Ø2.05只表达原图圆径，厂家未标明攻牙，通孔/内螺纹类型及现有螺柱连接方式待实物核对。上层保留Ø2.60。新件Ø3.0为本稿设计间隙，48边圆孔的网格最小通径略小，报告中单列，打印后还需校准。隔柱外径、螺头/垫片/工具空间均为占位，不冒称标准件规格。

先用 `mount_template.stl` 空载对四孔 → 核对上下板同轴及螺柱连接类型 → 安装四金属隔柱/上层板/带孔金属横梁 → 从上方紧固再安装斗体。维护时先移除斗体或在断电、机械支撑后抬斗，保持顶面工具通道开放；运输姿态的斗底会遮住上方长工具路径。前适配板和纵梁已给局部螺头/工具空间避让。主承力交给金属结构；打印样板不进入承力路径。

## 候选打印件与试装顺序

已确认Tina2C（100×100×100 mm、0.4喷嘴、无热床）和PLA，按[首件打开/切片指南](PRINT_PLA.md)在WiiBuilder导入四孔样板，保持mm/100%。样板70×98，98方向每侧仅1 mm，须检查裙边及实际可用区；相机座可放。雷达板70×110和底座50×120默认平放超界，暂缓这两件，不能缩放改变孔距；本轮没有设计分体板。

| STL | 默认包络 | 建议摆放和注意事项 |
|---|---|---|
| `exports/lidar_plate.stl` | 70 × 110 × 5 | 平底向下，无悬空桥接；试印孔槽校准片后再印整板 |
| `exports/camera_bracket.stl` | 约 48.87 × 64 × 43.39 | 平底向下，前板朝外倾 10°，两侧有筋；切片时检查外倾面/孔桥接是否需局部支撑 |
| `exports/base_adapter.stl` | 50 × 120 × 6 | 平底向下，紧凑前传感器适配板，保留四个底盘螺头维护空间 |
| `exports/mount_template.stl` | 70 × 98 × 2.5 | 平底向下，四孔58×86、设计Ø3.0；只用于对位，禁止承重 |

建议先量雷达、相机和车架孔位与设备外包络，改单件参数 → 切片查看孔和壁 → 小件试印 → 空载手拧试装 → 断电手动走完整翻斗行程 → 保持无人/无障碍的后方落料区，逐级增加假载荷并测总质量和重心。PLA试打通过后，长期材料、层间强度和螺栓预紧仍需核算，本稿未批准承载材料选型。

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

输出包括4个候选STL、固定柱距90/100对照，以及四孔58×86/68×96样板/框架/传感器适配板的检查网格，运输/卸料/机构/安装PNG、概览与 `geometry_report.json`。`*_check.stl`仅供检查，金属框架检查件含多个实体，禁止作为打印件。实际切片从样板和四柱网格测孔轴及通径，比较改孔距后同步，并检查实际前适配板的9.9 mm工具圆盘不被封堵。固定对照显式设M2.5、3.0孔、10工具径，生产单件继续采用用户当前源参数；用户改默认不会污染固定回归。报告不包含完整碰撞、有限元、打印质量、物理载重或传感器视野验证。

重新提取资料可运行 `$env:PYTHONPATH='E:\rober\tools\cad-python'; python docs/hardware/cad/ground_dump_v0/extract_mount_reference.py`，额外需要ezdxf（本机已放项目依赖目录）；设计打开与常规导出无需运行提取脚本。

## 资料来源与证据边界

- `docs/vendor/VENDOR_INDEX.md`：本项目硬件资料入口。
- `docs/vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl`：二进制 STL 共 546006 三角面，原坐标包围框 `[-86.1494,-91.5537,-35.7864]` 至 `[86.2494,102.4765,64.1528]`，轴向尺寸约 `172.3988 × 194.0302 × 99.9392`。**STL 自身不声明单位**；本稿将其当作毫米量级参考，长轴作为车长是设计假设。图中底盘采用简化盒体与轮子，并未导入原网格，不能用简化底盘测孔位或做严谨干涉检查。
- `docs/vendor/waveshare_wave_rover/WAVE ROVER DXF.dxf` 与 `WAVE ROVER-EP DXF.dxf`：本轮实际解析两板四孔，采用原始坐标/毫米单位及90°映射；详见上节及JSON。早期PDF无尺寸提取证据未参与本次孔距计算。
- `docs/vendor/lidar_pkg_ros2-main/models/lidar_mount.stl`、`urdf/lidar.urdf`：已查看参考包络。STL 原始包围尺寸约 `0.08 × 0.02953 × 0.14`，与底盘 STL 存在数量级差异，单位未核实，故未复用它的尺寸或孔位。URDF 中传感器图形也只作为示意。
- [OpenSCAD 官方下载](https://openscad.org/downloads.html)与官方站点链接的[用户手册：命令行](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Using_OpenSCAD_in_a_command_line_environment)：便携工具和导出参数入口。

底盘额定载荷未得到本地资料确认；2 kg 仅指垃圾目标，总载荷还包括斗、架、执行器、电池及电子件。丝杆推力和两端距离随翻转变化，运输状态接近低夹角，所需推力可能较大；需要实际机构计算、全行程防卡死、机械止挡、防夹、断电锁定和满载防倾覆评估。雷达扫描平面、相机视野、天线/散热/维修空间及线缆弯曲也需实物检查。本轮不修改 OKR 完成度。
