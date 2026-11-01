# 分体安装板实现与验证

状态：CAD实现与验证已验收，独立review无新增P1/P2，主节点已核对留档并授权Git交付。未切片、未实打、未验强度。

## 实际改动

- `ground_dump.scad`：两板各两片半搭接，雷达低/高舌与底座低/高舌打印入口分别翻面/居中，装配保留设备孔、立柱孔和底盘接口。Z搭接面贴合、肩侧XY0.2间隙；雷达偏心接头避开Ø65占位和线缆口。95/100柱距联动搭接，槽旁全厚材料余量至少1.2 mm。四个M3穿栓接头，头/母/垫/工具尺寸明确为采购前占位。
- 默认底座从旧Z118移到前梁顶130，柱脚联动136，雷达板310/相机222保持；修复已有板/梁正体积重叠。
- `export.ps1`、`validate.py`及新`verify_split.py`：生产/参考分区、原始网格逆变换、孔槽/接触/肩隙/通径、精确CSG内部相交见证、实际金属截面工具区检查。140加长板工具窗继续检查，不套用生产≤90约束。
- `exports/tina2c/`只放`lidar_lower.stl`、`lidar_upper.stl`、`base_lower.stl`、`base_upper.stl`及`PRINT_LIST.md`；四件逐个导入、分别打印，各1件。旧`lidar_plate.stl`、`base_adapter.stl`移除；新`lidar_plate_assembly_reference.stl`、`base_adapter_assembly_reference.stl`仅装配参考。
- `exports/`增加`split_parameters.echo`、`split_validation.json`、`base_metal_collision_check.stl`、`lidar_overlap_check.stl`、`base_overlap_check.stl`、`sensor_adapter_long_check.stl`、三张`split_*_raw.png`及`split_overview.png`，更新整机/回归产物。相机和四孔模板原STL经顶点/体积对比确认同形，保留原文件字节。
- `README.md`、`PRINT_PLA.md`、Tina2C参考仅同步当前分体尺寸、逐个摆盘、取件后的upper翻回装配、M3 BOM与风险。本轮六文档按阶段写入，未改OKR、vendor原图、工具、其他产品代码或既有sprint。

## 验证命令与结果

已读vendor索引、Tina2C本地参考及既有四孔原始DXF证据；机器100³/0.4/PLA边界沿用官方来源。本轮不新增底盘硬件事实。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs/hardware/cad/ground_dump_v0/export.ps1
git diff --check
```

最终默认完整导出链返回 **0**。OpenSCAD2021.01、Python3.13.12、trimesh5.2.0、numpy2.5.4；现有项目工具，无新增依赖。全套产物返回`EXPORT OK`，四生产件实测如下，均封闭/法线一致/单连通/正体积、Z0、平底面积>100 mm²、XY≤90、Z≤100：

| 生产半片 | 尺寸mm | 体积mm³ | 三角面 |
|---|---|---:|---:|
| lidar_lower | 70×87.9×5 | 27870.763 | 1628 |
| lidar_upper | 70×31.9×5 | 9110.439 | 616 |
| base_lower | 50×67.9×6 | 17820.527 | 608 |
| base_upper | 50×67.9×6 | 17820.527 | 608 |

核心输出：`PASS split interfaces: original slots/columns, coincident M3 axes, Z contact, XY clearance, no positive overlap`；`PASS split access: lidar envelope, base nut tools, 130/136 metal contact, 140 mm reference tools`。实际打印网格逆变换后，设备四槽(±17.5,±17.5)、柱槽(0,±45)、线缆口(-27,0)、底座柱孔(13,±45)保持；两半M3孔分别切片测同轴/3.4名义通径；接触Z为2.5/3，实际两肩间隙0.2。默认设备槽到全厚肩3.7、Ø8工具到Ø65占位净距3.098 mm。

三项CSG相交见证扣除1 mm³标记块后正体积为0；共享接触数值壳0.001 mm单列，另以真实STL测Z贴合，生产几何没有Z空气层。实际金属网格下移100后，在底座螺母高度按安装坐标采样Ø8工具圆盘均开放；底座梁顶/板底130接触、板顶/柱脚136接触。四孔58×86/68×96、9.9工具圆盘、140加长参考工具窗均PASS。

95回归：系统Temp复制源/脚本，保存`part=lidar_upper_print`、`mast_spacing=95`后执行完整export（显式项目工具/依赖），返回0；雷达两半70×89.9×5、70×34.9×5，其他接口/工具区及90/100固定对照均通过，预览仍整机。

100回归：Temp副本中用当前源、`-D mast_spacing=100`实际重导出四生产片、参数、金属框架及板梁碰撞见证，再运行验证，返回0。雷达两半70×89.9×5、70×37.9×5，实际槽肩余量2.7、工具净距1.7099；固定原设备孔和柱孔、Z/XY贴合通过。参考装配与检查件不混入生产目录。

负例：`part_id=9,lidar_plate_depth=60`及`part_id=11,base_length=100`均明确断言返回1，分别提示板深边距及生产预算；未忽略超界。140板仍可通过`part_id=8`实际导出并通过工具窗检查。

最后仅修改新手文字/图注后，`python validate.py exports`再检查已有网格，返回0；未再次改生产几何。view_image已查看打印/上下装配原图和裁切合成图，四灰盘明确为分别打印，接头上下工具侧可读。中文技术注释：SCAD114/559、export26/112、validate52/251、verify_split最终超过20%；本地链接和新增文本空白核对、`git diff --check`通过。

## 失败定位与修复

- 原方案Z0.2空气层经review指出会使夹紧舌片变形，实施前改Z贴合，仅保留XY肩隙。
- 100柱距初始方案槽旁只有0.7 mm余量，增加1.2最低材料边界，宽板搭接缩至8，实测100余量2.7。
- 初次CSG诊断把共享接触面输出为2D非流形片，严格诊断网格检查失败。将诊断限定到0.001 mm内部壳，生产几何保持Z贴合，真实STL验证接触；最终诊断只有封闭1 mm³见证块，返回0。
- 旧底座与前梁重叠经review实证，移至梁顶后实际相交见证/安装高度验证通过。

## 剩余风险与BOM

新增接头M3螺栓4、螺母4、垫片8，原底盘M2.5沿用；头母工具空间与螺栓长度为设计选择，采购与实装需复核。设备实物孔距仍待测，未切片/实打/验证PLA收缩、接头刚度、层间强度或紧固力矩；金属主架、丝杆、防夹和2kg垃圾及斗/架/执行器等构成的总载荷与防倾覆没有新增证明。样板98 mm边距问题不在本轮扩大修改。
