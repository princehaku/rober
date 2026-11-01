# Tina2C + PLA：先打开四孔样板

已确认机型 **ENTINA Tina2C**：成型体积 **100×100×100 mm**、0.4 mm喷嘴、1.75 mm PLA，**无热床**。[官方机型资料](../../../vendor/entina_tina2c/PRINT_REFERENCE.md)。先试四孔样板；原超界雷达板/底座已重做为四个原孔距分片，放在`exports/tina2c/`。PLA用于试装，金属承力方案和2 kg未验证边界保持。

## 第一件照着做

1. 官方Windows包已下载并解压：[双击本地WiiBuilder安装器](../../../../tools/wiibuilder/unpacked/Wiibuilder2.6.7.0_ENTINA_win.exe)，实际路径 `E:\rober\tools\wiibuilder\unpacked\Wiibuilder2.6.7.0_ENTINA_win.exe`（来自[ENTINA官方页](https://www.entina3d.com/pages/download-1)，本轮尚未运行安装器）。由你安装并打开，选择 **Tina2C、0.4 mm喷嘴及PLA预设**；若没有匹配机型配置先停下核对。GUI操作尚未验证，菜单可能随版本不同。
2. 在WiiBuilder使用“导入/打开模型”功能，选择 `E:\rober\docs\hardware\cad\ground_dump_v0\exports\mount_template.stl`。单位 **mm**、缩放 **100%**，尺寸应为 **70×98×2.5 mm**，居中、平面落床，关闭自动缩放适应平台。STL描述形状，切片器再为该机生成打印文件。
3. **98 mm方向居中后每侧仅1 mm余量**（70 mm方向每侧15 mm）。首件关闭支撑、brim和skirt，确认机型预设及所有附加路径仍在实际可用范围内。切片预览检查首层连续、孔贯通及边界；若软件仍提示超界/有效区小于98 mm，先停，不扩大机器边界或缩小样板。需要brim才能稳定时也先停，另行调整样板外缘或工艺。
4. 确认切片预览与Tina2C配置后，由你导出该机适用的G-code并按厂家TF卡（microSD）流程手动打印；直接把STL复制到卡里不能代替切片。本轮没有生成G-code或实打。
5. 实打冷却后空载核对M2.5四孔 **58×86 mm**，不强拧或扩动原金属孔。再量设备孔距，[四片清单](exports/tina2c/PRINT_LIST.md)中的STL要**逐个导入、分别打印，各1件**，mm/100%。示意图四张灰平面代表四次摆盘，不能把四件一起塞进100×100同一盘。高舌片已翻面落床，**切片时不要再次翻面或缩放**；取件后upper翻回，与lower台阶相搭，孔对齐、板面平齐后紧固。

## 0.4 mm 喷嘴建议起点

| 设置 | 本次试打建议 |
|---|---|
| 材料、温度、速度、冷却 | Tina2C PLA预设；无热床，不能套用其他机型的热床加热设置 |
| 层高 / 首层 | 0.20 / 0.20 mm |
| 壁数 | 3道；相机座可从4道起 |
| 顶层 / 底层 | 各4层，最终看切片预览连续封面 |
| 填充 | 20%，保留预设填充图案 |
| 支撑 / 附着 | 样板关闭支撑/brim/skirt并核对所有附加路径；相机座按孔顶预览决定局部支撑 |

这些数值是本项目试打选择，尚未切片或实打确认；增加填充和壁数不等于通过承载验证。

## 四件的朝向与支撑

| 文件（均在 `exports/`） | 默认尺寸 mm | 原始落床面与支撑判断 |
|---|---|---|
| `mount_template.stl` | 70×98×2.5 | 理论可放，98方向每侧仅1 mm；框形平底向下、四孔轴竖直，无需支撑 |
| `tina2c/lidar_lower.stl` | 70×87.9×5 | 雷达低舌大片，原方向落床，1件 |
| `tina2c/lidar_upper.stl` | 70×31.9×5 | 雷达高舌小片，已翻面落床，1件 |
| `tina2c/base_lower.stl` | 50×67.9×6 | 底座低舌片，原方向落床，1件 |
| `tina2c/base_upper.stl` | 50×67.9×6 | 底座高舌片，已翻面落床，1件 |
| `camera_bracket.stl` | 48.870×64×43.392 | 可放；**42×64水平底板向下、斜板立起**，支撑见下段；先核对相机尺寸 |

相机斜板只偏离竖直10°，可先按原方向检查；它的两个约3.4 mm安装孔近水平方向贯穿，孔上沿会出现短桥接/悬垂。重点逐层看孔顶、外倾面的新生轮廓：若出现无承托线段、切片警告，或该机桥接能力尚未验证，在相应孔顶/外倾区加**可拆的局部支撑**，确认预览确实生成且取出通道可达；不要把整件孔槽塞满支撑。常规外倾壁有前层承托时可先不加该处支撑，最终依实际切片和试打决定。[Prusa：打印朝向与悬垂](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

四个新半片默认XY最大87.9，100平台名义边界余量至少6.05 mm；仍要预览brim/skirt和实际可用区。四片接头共新增M3螺栓4、螺母4、垫片8，按[装配说明与BOM](README.md#分体装配与新增bom)拼合，底盘M2.5沿用；头上母下、搭接Z面贴合，不用胶水承担接头。整板`*_assembly_reference.stl`、`*_check.stl`均不供打印，旧同名超界板已停止导出。PLA长期上车与强度仍待验证。[Prusa：PLA](https://help.prusa3d.com/article/pla_2062?product=mini)、[层高与壁数](https://help.prusa3d.com/article/layers-and-perimeters_1748)
