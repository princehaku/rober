# 2026.06.29 23:59 PC 地图雷达点动作卡证据

sprint_type: micro

## 设计先行

本轮只推进 PC 端“地图雷达点所见即所得”的结构化验收，不新增控制按钮。现有白话文案已经能说明“旧点不贴当前图”，但外部脚本和 DOM smoke 仍需要稳定字段直接判断当前地图到底画了几个雷达点，因此把证据放进 `action_status_cards[].id=radar_map_points.evidence`，普通首屏继续保持简易风格。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlActionStatusCard` 新增可选 `evidence` 对象，包含 `current_on_map`、当前点数、来源点数、frame 和阻塞原因数组。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `radar_map_points` 动作卡输出结构化证据；当前雷达点缺失时 `current_point_count` 固定为 `0`，旧来源点只进入 `source_point_count`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通动作卡 DOM 增加只读 `data-current-on-map`、`data-current-point-count`、`data-source-point-count`、`data-frame-id`、`data-source-frame-id`、`data-blocked-reasons`，可被现场脚本读取。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 DOM 上能读到“当前图 0 点、旧来源 81 点”的区别。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 `/api/robot-control/summary` 生成的 `radar_map_points.evidence`。
- `pc-tools/README.md`
  - 同步记录新的只读字段合同和不发送控制命令边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`，1 passed / 167 skipped。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "routes the sensor shortcut from structured action cards instead of camera wording"`，1 passed / 217 skipped。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，386 passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node *:7001 (LISTEN)`。
- 通过：只读 live spot check `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `radar_map_points.evidence.current_on_map=true`、`current_point_count=72`、`source_point_count=81`、`frame_id=laser_frame`。

## 剩余风险

- 本轮是 PC 只读合同和 DOM 验证；live spot check 只读 summary，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实车上的摄像头无首帧、Nav2 轮速 L/R 非零、自由移动真实运动仍需要现场安全确认后单独复验。
