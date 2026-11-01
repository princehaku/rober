# Tina2C 首件导入与平台尺寸核对

sprint_type: micro

状态：文档与尺寸核对完成，主节点审阅通过；按授权交付本轮五份文档。未安装切片器、未切片、未生成G-code、未实打。用户提供`https://entina3d.cn/tina2c#specs`，本轮机型确认为Tina2C、材料PLA。

## 最小计划与实际改动

- owner：robot-hardware-engineer，单owner文档micro；不改CAD/STL/工具/既有sprint，不改OKR。
- 只读核对官方机型资料与四件生产STL的真实包围尺寸；一到两页指南优先教会WiiBuilder打开样板，拒绝缩放孔距。
- `PRINT_PLA.md`：明确100³、0.4喷嘴、1.75 PLA、无热床及官方软件入口；加入绝对STL路径、mm/100%、98方向仅1 mm余量、停用/检查brim/skirt和有效区；样板先行，相机可放，两块板默认平放超界暂缓。
- `README.md`：仅同步打印相关入口及两件超界事实。
- 新增`docs/vendor/entina_tina2c/PRINT_REFERENCE.md`与vendor索引简短入口：保存URL、2026-11-01日期、规格、来源差异及未切片边界，不保存网页或程序包。

## 验证命令与结果

已读`docs/vendor/VENDOR_INDEX.md`、现有CAD说明及`mount_reference.json`孔距证据。官方国际产品页确认100×100×100、0.4喷嘴、1.75 PLA、无热床、WiiBuilder/Cura及TF工作流；国内页web工具失败，用`Invoke-WebRequest -Uri 'https://entina3d.cn/tina2c' -UseBasicParsing`取得HTTP200、202661字符，去标签后读出100³、1.75 PLA、WiFi/USB/TF与70 mm/s。国际FAQ写100 mm/s，差异只留参考文档，指南不设置最高速度。软件下载页入口由主节点核实，本轮未假称GUI操作已验证。

实际只读执行（`PYTHONPATH=E:\rober\tools\cad-python`）：以trimesh逐件加载`exports/{mount_template,camera_bracket,lidar_plate,base_adapter}.stl`，打印`mesh.extents`、`(mesh.extents<=100).all()`、`(100-mesh.extents[:2])/2`，返回0。

| STL | XYZ尺寸mm | 原方向在100³内 | 居中XY每侧余量mm |
|---|---|---|---|
| mount_template | 70×98×2.5 | true | 15 / 1 |
| camera_bracket | 48.870×64×43.392 | true | 25.565 / 18 |
| lidar_plate | 70×110×5 | false | 15 / -5 |
| base_adapter | 50×120×6 | false | 25 / -10 |

样板孔距沿用前轮DXF实取58×86，M2.5为用户确认，新件3.0通孔为设计间隙。包围尺寸比较未替代软件有效区及实际切片：未改缩放、未改孔距、未设计分体板。本地Markdown链接、mm/100%与四件尺寸文字核对通过，`git diff --check`返回0。

## 剩余风险

98 mm方向仅1 mm边缘余量，实际机型预设的禁区、裙边/启动附加路径仍可能超界；遇到超界先停，不扩大机器边界或缩小孔距。雷达板和底座默认平放超界，设备实测孔距也未确认，后续另定改板/分体/更大机器方案。相机孔顶支撑需实际预览，所有切片、实打、PLA长期上车、金属承力及2 kg负载验证仍未完成。
