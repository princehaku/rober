# 榫卯主底板实际交付记录

sprint_type: epic

状态：主节点与独立只读复核已验收CAD范围，未实打；已获Git交付授权，正在提交推送。owner：robot-hardware-engineer。

## 实际改动

新 `docs/hardware/cad/main_deck_v0/`：参数化OpenSCAD、可重复PowerShell入口、轻量Python网格/装配检查、真实STL预览排版、README、六面板/七桥键及三档接头和单安装座试片。旧ground_dump README仅加新底板入口/小适配板区别，Tina2C参考仅加链接。未更改旧模型、工具、vendor原图或无关sprint。

用户“用榫桙结构 不要弄金属条”覆盖先前金属方案；新结构无金属条。五M3沉头螺栓只作桥键止退，双背面燕尾＋厚肋＋四柱是几何传力路径。用户进一步确认柱顶外牙约5mm，故将四Ø22全高座改为Ø10顶窝＋默认2mm夹底，Ø3通孔；不沿用12mm全厚夹持或新增长M2.5螺丝假设。0.5mm垫/2mm母均设计包络，仅剩约0.5mm牙，不承诺有效啮合。

## 实际验证命令与中间结果

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs/hardware/cad/main_deck_v0/export.ps1
$env:PYTHONPATH='E:\rober\tools\cad-python'
python -B docs/hardware/cad/main_deck_v0/build.py --openscad E:\rober\tools\openscad\openscad.com --verify-existing
python -B docs/hardware/cad/main_deck_v0/build.py --openscad E:\rober\tools\openscad\openscad.com --images-only
```

首个入口实际生成13生产STL＋10试片；全部封闭、绕序一致、单连通、正体积、Z0、XY≤90/Z≤100。六板52.34154 /69.4 /77.05846 ×79.7×12；H键42×42.04154×9、32×59.4×9、32×66.75846×9，V键各42×55.4×9。

已从实际STL逆变换/切片验证：58×86四轴与3mm通孔、Ø22全高外周/2mm夹底/Ø10窝、板中心偏置-22.641541、男燕尾6→14×6、正式件/试片同截面、0.3侧/顶间隙。实际网格CGAL见证检查最终整键/面板零正体积穿透、7键×6位置插入采样、Z/跨缝位移约束、内部两键端墙止退、五止退轴及下方工具空间。采样不等于连续全程运动仿真。

首个PowerShell入口实际完成生产导出，负例输出解析失败返回1；修复后复用同一批生产STL执行完整检查，最后两个Python命令均返回0。没有重复导出已通过且未修改的生产几何；后续源改动仅为注释/参考步骤图。报告源SHA256与最终SCAD逐字节一致：`f4539c397fe6ac9b4ec03d46d255baa0971fc72428c3cce20149375544452518`。版本OpenSCAD2021.01 / Python3.13.12 / numpy2.5.4 / trimesh5.2.0。

```text
PASS actual STL four axes 58x86; D3 bore; D22 full-height rim; 2mm clamp/D10 recess; offset
PASS actual STL dovetail: male 6->14x6, side clearance 0.3, roof clearance 0.3
PASS actual STL final overlap/42 insertion stages; Z/cross locks; 2 wall stops; 5 bolt stops/tools
PASS coupon identity; dovetail slopes <=45deg; ONLY recessed seat rings need local support
PASS parameter c0.2/c0.4/thickness14; oversize/thin/loose rejected
PASS MAIN DECK: 13 production + 10 coupons; mesh/interface/path/lock/regression checks
PASS images regenerated from existing production STL
```

实际报告中最终交集/42采样交集均0 mm³；故意位移后的Z约束2055.026、跨缝465.368、两个端墙约168、五个止退各14.942 mm³，证明诊断不会始终空通过。三个不可行参数均返回1且含Assertion，按预期拒绝。0.2/0.4公差真实槽边/顶、14mm板厚及对应桥键有效；未以参数回显代替网格。

## 失败定位与修复

- 主节点只读发现面板逆变换Rx180后额外倒面；已移除错误倒面，并在逆变换后断言法线一致、正体积。单轴反射/XY交换仍按需倒面。
- 首轮负例触发OpenSCAD中文断言时，Python默认GBK读取UTF-8输出失败；改为显式UTF-8后进一步确认Windows版断言实际写stdout，已统一检查stdout+stderr。三个负例局部复验均返回1且读到Assertion，随后完整验证返回0。不关闭参数断言，不重复无改动的生产CAD导出。
- 中间OpenCSG图有内部接触条纹；最终改用真实导出STL拼合。自动取景曾裁掉外轮廓，已改显式中心/旋转/视距560~650；先查看完整顶视，再全套渲染、查看overview/steps并移动P标签避开孔号。图像不用于替代实体穿透证据。

## 资料与风险

已读AGENTS、vendor索引、WAVE ROVER / EP本地DXF及既有坐标JSON、Tina2C官方参考。原始上孔2.6、下层图示圆2.05、单位mm/比例1保持；只采用四轴和车体参考偏置，不虚构厂商额定载荷。Prusa官方打印建模/连接切分资料只支持方向与试配原则，未提供本设计承载证据。

面板顶朝床后四安装窝底是径向3.5mm环形桥接，必须窝内局部支撑、清理并先打单座；燕尾自身开放斜面≤45°。未安装/运行切片器、未生成G-code、未打印/上车/HIL/加载。先单座试原柱/螺母，再同档燕尾试配，必要时改源公差重导全套，最后逐级加载。2kg是垃圾目标，总附加载荷含斗/架/执行器；PLA层间、蠕变、冲击和唇口强度均未验证。

独立review最终结论：CAD试装稿范围通过，无未解决P1/P2；已核对实际网格报告、源哈希、42采样、正约束、回归、完整预览与打印清单。主节点亦已读报告/图。未将几何通过转换为承载/打印通过，未改OKR。

最终文本检查：`git diff --check`通过；四Python文件AST语法、相对文档链接与新增文本无尾空格通过。五源码中文注释占非空行分别build22.56%、export23.08%、SCAD21.63%、排图23.81%、verify21.50%，均超过20%。清理本轮pyc缓存与相机调试图，只保留生产/试片STL、最终参考PNG和验证JSON；原无关2026.06.12未跟踪目录保持。Git只交付本轮main_deck、两个文档链接和本sprint六文档，提交推送事实由最终命令输出报告。
