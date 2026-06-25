# PC 雷达地图扫描范围 Micro Sprint

## sprint_type

micro

## 实际改动

- 在普通首屏地图视口新增 `plain-map-radar-sweep` 只读 overlay。
- 雷达已运行或待刷新时，地图上显示半透明扫描扇区；有 AMCL/map-frame 位置时跟随机器人 marker，缺定位时居中显示虚线占位并说明等待机器人地图位置。
- 保留既有文字 marker、机器人 marker、路线和目标 overlay，不新增 scan 点云解析，不触发雷达启动、手控、Nav2、stop 或 delivery。
- 更新 PC 工作站文档和 App 测试，锁定已运行、待刷新、缺定位和有定位场景。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、154 个测试通过；覆盖雷达已运行缺定位、有定位跟随机器人、雷达待刷新三种地图 overlay 状态。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 和 `vite build` 通过。
- 通过：`git diff --check`。
- 通过：7001 DOM/API smoke；当前真实 summary 的 LiDAR 字段为 `not_loaded`，页面正确显示 `雷达未运行` 且不渲染 sweep；`safe_to_control=false`、`robot_control_executed=false`。本 smoke 未启动雷达、未点击控制按钮、未发送 manual/keyboard/Nav2/stop/delivery。

## 剩余风险

- 当前 overlay 是雷达运行/待刷新状态的范围可视化，不是逐点 scan 点云；真实点云所见即所得仍需要上位机提供安全限量 scan 点或栅格投影合同。
