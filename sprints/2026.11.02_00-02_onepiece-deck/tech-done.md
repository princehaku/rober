# 一体底座代打稿

sprint_type: micro

状态：CAD范围已由主节点与独立review最终验收通过，无未解决P1/P2；已授权Git交付，尚未切片/实打/承载验收。owner：robot-hardware-engineer。

## 实际改动

用户“等等 你先弄底座 我看看是不是别的代打”。新增 `docs/hardware/cad/main_deck_onepiece_v0/`：可编辑SCAD、PowerShell导出入口、轻量Python导出/截面测量/排图、README代打说明、`exports/main_deck_onepiece.stl`、顶/底PNG与overview、dimensions.json。原main_deck README仅加一段一体版入口，原分块SCAD/STL不改。

整体200×160×12，板中心X=-22.641541；四轴58×86、Ø3通孔、Ø22座外圈、Ø10顶窝、2mm夹底沿用。去掉七个旧燕尾槽、五个M3止退孔和所有分缝，没有桥键/金属条。原blank圆端筋会越过边界，保留一次整板intersection裁剪，未把含槽carved_deck冒充一体版。STL已安装顶面朝床，图逆变换回使用姿态。

本轮斗体暂停草稿仍仅保留未提交3文件；暂停记录同步“用户已选全分块打印、按最新要求先做底座”，不随底座提交。

## 实际验证

从系统临时目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File E:\rober\docs\hardware\cad\main_deck_onepiece_v0\export.ps1
```

OpenSCAD2021.01，每次子调用检查返回码、非空和stdout+stderr的ERROR；最终入口返回0。真实STL实测外包络200×160×12、封闭、绕序一致、单连通、正体积326219.176235 mm³、Z0；直接恢复安装姿态切片拟合四轴±29/±43、孔外接径约3.000001/最小通径2.993574、窝外接径约10.000001/最小通径9.978585；台阶上下实体状态证实2mm夹底，三个高度检测座外圈连续。

```text
PASS mesh: [200.0, 160.0, 12.0] watertight/consistent/positive/single/Z0
PASS actual sections: four axes 58x86, D3/D10, 2mm clamp, D22 outer rim
PASS filled: old 7 slots, 5 stop holes, all former seams; only 4 mounting interfaces
PASS two CAD views rc0/no ERROR; onepiece export complete
```

旧七槽在14处原榫截面点为实体；五止退轴中心/周边在高低截面均填实；旧X=-70/0与Y0分缝上下/中心采样均连续，顶皮仅四窝开口。只测当前单件，未运行旧榫卯套件/ROS。

已view顶/背完整轮廓和四窝，主节点与独立review核对图/JSON均通过，无机械P1/P2。图中“1件/比例100%”纯排字更新，复用现有CAD原图，不重导已通过几何。

最终文本/语法：Python AST、README相对链接、源/STL与JSON哈希一致、新文本无尾空格、`git diff --check`均通过；PowerShell保留UTF-8 BOM。中文技术注释占非空行：SCAD21.79%、PowerShell21.43%、Python21.20%。仅当前一体目录9文件、分块README入口和本micro留档待交付；斗体暂停草稿及原2026.06.12无关目录保持未提交。

## 失败定位及修复

最初截面环重建在二进制STL邻接三角交点出现约0.00001mm舍入差，固定小数舍入使同一点落在两格，环度数不为2。真实网格封闭检查一直通过；改为0.0001mm邻格点焊接后所有截面通过，不改变/修补生产网格。源/实际STL哈希写入JSON供复核。

## 资料、未验证项及下一步

已读AGENTS、vendor索引、两份本地WAVE ROVER DXF、原始孔位JSON；本轮再次读取原图单位mm，上孔2.6、下层图示圆2.05保持独立。用户确认四柱外露M2.5螺杆约5mm；柱高、原螺母/垫片和工具仍需实配，不假定长螺栓或内牙柱。

代打1件，单位mm、比例100%禁止缩放，PLA试装；200×160超Tina2C100³，需更大有效平台。顶面朝床，四窝底局部支撑须清理。先用原单座试片核短外牙夹紧、不顶死/压裂，再整体空载试装；2mm底＋0.5垫＋2mm母仅为设计包络，约0.5mm余牙不证明有效啮合。2kg是垃圾目标，垃圾＋斗架/执行器等总附加载荷、PLA层间/蠕变/刚度均未验证。未选代打商、未切片/打印/上车，不改OKR。

Git交付范围仅一体目录9文件、分块README入口及本记录共11文件；斗体两目录和原无关sprint均保留未提交。提交推送结果由最终命令输出提供。
