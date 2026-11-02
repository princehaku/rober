# N20 打印推举机构实施计划

> 实现采用 superpowers:subagent-driven-development；硬件 owner 单线实现并负责验证，顾问只读复核，主节点负责验收。

**Goal:** 把原示意执行器替换为参数化 N20 打印螺杆机构，并交付整车运动预览及可打印试装零件。

**Architecture:** 并排电机经打印正齿轮驱动粗牙螺杆；防转螺母带输出推杆，两端铰接。螺杆轴肩通过独立止推壳向下铰传力，电机输出轴只传扭。电机未知尺寸保留参考标识和可替换轴套。

**Tech Stack:** OpenSCAD、现有 Python CAD 依赖、现有串行渲染工具链。

**Spec:** [prd.md](prd.md)。状态：边界、文件范围和验收命令完整，可开始实现。

## 全局约束

- CAD/集成实现 owner：dump_model；mechanism_review 做独立几何/制造复核，并在参数证据齐全后独占归档下述vendor文件。两者文件范围不重叠；主节点不执行实现或测试命令。
- 保留四孔 X±29/Y±43、后轴 X=-105；斗中心 -20→-15，框长梁边界 [-120,82]→[-115,87]；雷达杆 X76→81、中心110→115；相机不动。连接四孔的横梁不随空框漂移。
- 斗仍为180×200×70、完整四壁含固定低后斜壁、0–40°；无活动门、无金属加强条。
- 驱动候选采用并排 N20、1:1 齿轮、单线螺纹外径10 mm/导程2 mm、有效牙长约52 mm、螺母长约16 mm；这些是设计输入，允许按封装核算调整并记录原因。
- 约80.16 mm闭距/32.77 mm行程只作原几何起点，必须计入轴颈、止推、端挡、防转与啮合长度；必要调整上下耳坐标，但须重验整车空间，不能靠相交豁免掩盖封装失败。
- 电机壳与轴规格未确证：使用有一手出处的参考包络或明确的设计占位；不得把该来源视为用户型号。实配状态保持待验证。
- 后续输入已补齐：用户商家图纸给出12×10×24.1 mm主体、D轴3 mm/外露10 mm；用户确认3V 60RPM。按商家尺寸建可调接口，实际打印公差和连续扭矩仍待实配。上条未知条件仅适用于未有来源的剩余字段。
- 螺纹、螺母、齿轮必须有真实配合几何；独立止推及双向传力路径可检查。0°支承、机械终挡、手动检修锁止孔、限位开关安装预留纳入图；端挡不能代替断电限位。
- 技术注释中文且超过20%。不改ROS、电气参数、控制器、OKR比例，不采购或运行硬件。

## 文件范围

允许主责新增 `docs/hardware/cad/n20_printed_drive_v0/`（SCAD、verify.py、export.py、README及STL/PNG/JSON导出）。允许修改 `docs/hardware/cad/compact_dump_v2/` 当前源、验证/渲染和导出、README；`docs/hardware/dump_as_built_plan.md`、`docs/images/dump_as_built_plan.svg/.png` 与 `docs/hardware/cad/main_deck_onepiece_v0/README.md` 当前入口。

厂商事实归档独占交由mechanism_review：新建 `docs/vendor/n20_reference/REFERENCE.md` 并在 VENDOR_INDEX.md 加索引；保存必要事实及链接，不复制整份网页。用户后续提供的三张产品截图允许存入该reference目录作为商家图纸证据，先读图核实机械参数；对照厂商与用户商品来源分开标注。dump_model从分工调整起不改vendor范围，统一最终交付验收。主责可更新本 sprint 的 tech-done.md，主节点维护其余阶段文档。

不修改历史生产板SCAD/STL、旧 dump_kinematics_v1/ground_dump_v0、00-05及更早 sprint、用户照片、三个既有未跟踪目录。

## 实施任务与验收

- [x] 1. 按新前移参数设计驱动真实封装，列扭矩/推力公式、未知电机输入、标准件BOM、额外打印件清单。确认防转与双向止推路径后建模。
- [x] 2. 输出驱动独立装配、分件、螺纹和轴套试片。单件名义包络目标≤95 mm，100 mm成型空间包含摆放方向说明；螺杆若过长应合法拆分/重新封装，不缩放螺距蒙混。
- [x] 3. 驱动几何验证：单件网格闭合、包络、输出行程、最小螺纹啮合/导向搭接、螺纹转角与位移关系、齿轮节圆与相位、双端保留量、实质非法参数拒绝。输出独立哈希证据。
- [x] 4. 整车全角去回验证真实驱动外形与框/斗/电子/传感器，保留实际后斜壁落料路径及直接竖落失败结果，保持未知整车CG不认证。不要继续沿用旧绿色圆筒碰撞模型。
- [x] 5. 生成整车运输/半程/抬起及动画、驱动局部与爆炸图；复核图注、源哈希、STL清单、中文说明、限位/标准件是否齐全。
- [x] 6. 独立复核后修复，更新本轮实测范围与风险。限定文件的提交与显式推送结果由交付回执记录。

命令由主责执行并记录真实输出：

```powershell
$env:PYTHONPATH='E:/rober/tools/cad-python'
python -B docs/hardware/cad/n20_printed_drive_v0/verify.py
python -B docs/hardware/cad/n20_printed_drive_v0/export.py --openscad E:/rober/tools/openscad/openscad.com
python -B docs/hardware/cad/compact_dump_v2/verify.py
python -B docs/hardware/cad/compact_dump_v2/render.py --openscad E:/rober/tools/openscad/openscad.com
git diff --check
```

本轮不建立硬件性能通过阈值。额定/堵转扭矩、打印摩擦及新增斗重未知时，只输出需求计算与条件，不宣布0.5 kg可举、断电自锁或防翻成立。试片网格通过不等于实物配合通过。

## Review focus

1. 螺杆轴向力是否经独立轴肩/止推壳闭合到下铰，电机轴不能充当止推件。
2. 所有行程中实际牙形和齿轮相位是否正确，输出杆是否有防转而非只画圆筒。
3. 电机尾部/齿轮盒、输出端和手动锁止件是否穿框、穿斗或侵入线束。
4. 标准件、打印朝向、牙形试片、装配顺序能否让用户实际试装；未识别电机接口不得冒充匹配。
5. 前移改善只以同一载荷假设比较，出口竖落风险及真实CG未知不得被通过摘要遮盖。

## OKR 最低优先级核对

当前OKR.md 4.1最低为 O10 约12%。本轮服务送达后卸料的机械设计，CEO明确指定 N20 和平台前移；不替代 O10 的AMCL/Nav2或HIL验收，不改变任何完成比例。最终复盘核对该理由是否仍成立。
