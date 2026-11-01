# PLA首次试打指南

sprint_type: micro

状态：文件与几何检查完成，主节点已审阅通过；未切片、未生成机器G-code、未启动物理打印。用户要求“继续看怎么3D打印？”，并指定PLA；打印机/喷嘴型号仍待确认。本轮不改OKR完成度。

## 最小计划

- owner：robot-hardware-engineer。只写PLA指南、README打印链接及本micro记录；不改SCAD、STL、原导出图、vendor、工具或旧sprint。
- 流程：读资料和已有验证入口 → 检查四件STL实际落床面/边界/体积/封闭与连通 → 一页指南，先四孔样板再传感器件 → 核对链接、mm/100%和空白。

## 实际改动

- `docs/hardware/cad/ground_dump_v0/PRINT_PLA.md`：五步首件流程、约六行参数表、四件朝向/尺寸表；明确0.4 mm喷嘴是假设起点，温度/速度/冷却使用机型与耗材厂商PLA预设。相机座42×64水平底板落床，10°外倾壁和近水平孔顶逐层预览后决定局部支撑。
- 同目录 `README.md`：增加指南链接，同步PLA用于试装、长期承载材料仍待验证的说明。
- 本文件记录实际证据；未新增图片，未改现有模型或工具依赖。
- 审阅后明确金属方案限主架、隔柱及翻斗/执行器承力连接，斗体材料和工艺继续待定；按授权提交这三份文档，保留未切片/未实打边界。

## 验证结果

已读本地来源：`docs/vendor/VENDOR_INDEX.md`、现有SCAD/README/`mount_reference.json`，并用ezdxf只读重查两DXF原孔实体：上层INSUNITS4，四孔直径2.6；下层INSUNITS4，四圆直径2.05。用户M2.5安装事实、新样板设计通孔3.0及58×86孔距沿用已核实边界，未把样板孔径当成厂家原孔。

官方来源核实：[PLA](https://help.prusa3d.com/article/pla_2062?product=mini)、[层高与壁数](https://help.prusa3d.com/article/layers-and-perimeters_1748)、[面向打印的建模](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)。直接PLA无query链接一度超时，检索到同一官方文章的product=mini地址后成功读取。指南没有照抄Prusa温度来配置未知机器。

实际命令（仓库根）：

```powershell
$env:PYTHONPATH='E:\rober\tools\cad-python'
$cadPrintCheck=Join-Path $env:TEMP ('rober-pla-guide-check-'+[guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath 'E:\rober\docs\hardware\cad\ground_dump_v0\exports' -Destination $cadPrintCheck -Recurse
python docs/hardware/cad/ground_dump_v0/validate.py $cadPrintCheck
git diff --check
```

已读validate.py：入口需要输出目录且会写报告/PNG，因此只在Temp副本运行，返回0，所有现有网格/孔距/工具空间检查通过；仓库exports未重导出或改写。

另以trimesh直接读取四个生产STL，核对边界、底面三角形、法线及体积：四件均封闭、单实体、正体积且最低Z=0（单实体结果由既有validator的独立并查集检查给出）。

| 文件 | 实际边界尺寸mm | 体积mm³ | Z=0落床面积mm² |
|---|---|---:|---:|
| mount_template | 70×98×2.5 | 4689.578 | 1875.831 |
| lidar_plate | 70×110×5 | 37141.735 | 7428.347 |
| camera_bracket | 48.870×64×43.392 | 27591.447 | 2602.282 |
| base_adapter | 50×120×6 | 35809.693 | 5968.282 |

相机底面实际XY边界[-21,-32]至[21,32]，为42×64底板；大面积斜板网格法线换算偏竖直10°，与SCAD一致。两个约3.4 mm近水平穿孔的孔顶存在短桥接/悬垂，指南没有统一关闭该件支撑。未发现本轮需要修改几何的关键缺陷。

附加检查脚本曾调用trimesh.body_count触发缺少可选scipy；未安装新库，改用已有validator已通过的并查集连通证据，实际底面/法线测量重跑返回0。链接本地目标、mm/100%文字及文档行尾空白均检查通过；最终`git diff --check`返回0。

## 剩余风险

本轮证据仅为既有文件/几何与打印流程指导；打印机、喷嘴、具体PLA品牌、切片桥接/支撑和实打质量未确认。先样板四孔对位，再确认设备实物尺寸；主架仍采用金属，PLA长期上车、紧固和2 kg负载未验证。未据有限PATH/Program Files查询断言全机无切片器。
