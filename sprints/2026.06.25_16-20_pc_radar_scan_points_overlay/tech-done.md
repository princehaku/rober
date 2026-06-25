# PC 地图雷达点位 Overlay

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 Robot Control summary 增加 `scan_preview_points`、点数、来源点数和 frame 字段，作为地图雷达点位的只读合同。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 `/api/radar/scan-proof/latest` 或 `/api/radar/status` 的结构化 scan 点，或 LaserScan `ranges + angle_min + angle_increment` 抽样生成相对雷达点；无点位时保持空数组，不伪造点云。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 与 `src/styles.css`：普通首屏地图在有 AMCL/map-frame 位姿和 scan 点时渲染小点 overlay；缺点位或缺定位时显示短状态，不暴露 raw/ranges 工程字段。
- `pc-tools/workstation/test/App.test.ts`、`test/catalog.test.ts`：覆盖 summary 从 ranges 解析点位、地图 overlay 渲染点位，以及默认缺点位时显示“雷达点位未读取”。
- `docs/product/pc_tools_workstation.md`：同步记录本轮 scan preview 点位合同和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，2 个 test files、154 个 tests。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，完成 app/server TypeScript 与 Vite production build。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 smoke：`/api/health` 返回 PC readonly workstation；`/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`lidar_lifecycle_running=true`、`latest_scan_proof_fresh=false`、`scan_preview_point_count=0`、`safe_to_control=false`。本轮没有点击或调用 radar start、Nav2 execute、manual、keyboard、stop、delivery 或 `/cmd_vel`。

## 剩余风险

- 当前点位是相对机器人/雷达的局部轮廓 overlay；如果上位机没有提供真实机器人 x/y/yaw，PC 不会把点转换成全局地图坐标，避免假 WYSIWYG。
- 真实逐点地图配准仍需要上位机进一步提供带 map-frame pose/tf 的 scan 点或栅格化局部点云合同；本轮没有启动雷达、Nav2、manual、keyboard、stop、delivery 或 `/cmd_vel`。
