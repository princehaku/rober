# PC minimal safety gate readback

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary.safe_command_boundary` 新增最小门禁白话字段：
  - `nav2_goal_minimal_precheck_plain`
  - `keyboard_minimal_precheck_plain`
  - `free_roam_motion_minimal_precheck_plain`
  - `free_roam_mapping_acceptance_plain`
- 外部脚本只读 summary 时可以直接区分：
  - Nav2 图上路线执行只复核现场安全确认和固定白名单。
  - 键盘启用本身不发车，只有按住方向键/WASD 才发送低速短脉冲。
  - 自由移动只要求现场安全确认和停止兜底。
  - 画面首帧、雷达新鲜、地图记录和地图画面只影响建图验收。
- `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - `Test Files 1 passed (1)`
  - `Tests 38 passed | 120 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仅输出 chunk size warning，构建成功。
- 通过：7001 只读 summary 验证。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001 (LISTEN)`。
  - `GET /api/robot-control/summary` 返回四个最小门禁白话字段。
  - live summary 显示 `nav2_goal_ready=true`、`keyboard_control_start_ready=true`、`free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`。
  - live summary 同时保持 `manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`command_dispatch_enabled=false`、`safe_to_control=false`、`robot_control_executed=false`，确认本轮验证未执行真实控制动作。

## 剩余风险

- 本轮只补只读 summary 字段，不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实路线执行、自由移动或键盘脉冲 HIL 验证。
