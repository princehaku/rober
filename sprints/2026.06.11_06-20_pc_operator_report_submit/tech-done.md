# PC Operator Report Submit

## sprint_type

micro

## 本轮目标

为 PC Robot Control 高级诊断补“现场 HIL 材料提交”入口，让现场人员可以从 workstation 把 motion/HIL 前置材料提交到真实上位机固定 `/api/operator/report`。普通用户首屏继续保持五张简单卡片，不暴露 HIL、delivery_success、structured_hil_claims、外部视频、轮速反馈等工程词。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlOperatorReportRequest`、`RobotControlOperatorReportStructuredHilClaims`、`RobotControlOperatorReportProxyResponse`。
  - 更新 Robot Control proxy policy contract 文案为 `status_latest_readback_plus_fixed_control_and_report_proxies`。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增固定 client API `postRobotControlOperatorReport(baseUrl, body)`。
  - 仅拼接 workstation `POST /api/robot-control/operator/report?baseUrl=...`，不允许组件传上位机 endpoint。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `buildOperatorReportProxy()`。
  - 上位机远端路径固定为 `/api/operator/report`。
  - body 白名单只允许 operator report 字段；未知字段、错类型字段和顶层危险字段 fail-closed 400。
  - 响应顶层固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
  - 只豁免 `structured_hil_claims.delivery_success` 这类精确人工 claim 路径；其它危险 true 仍 blocked。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/robot-control/operator/report?baseUrl=...` Express route。
- `pc-tools/workstation/src/server/catalog.ts`
  - 导出 `buildOperatorReportProxy()` 供测试覆盖。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在默认关闭的 `高级诊断 -> 现场 HIL 材料` 中新增 evidence_ref、site_state、各类 ref、operator_notes、checkbox claim 和“提交现场材料（高级）”按钮。
  - 提交成功或失败后显示最近 submit 状态、HTTP、失败原因、rejected fields、dangerous fields 和 request claims，并自动刷新 Robot Control summary。
  - 未改动 `.robot-console-grid` 五张首屏卡片。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖固定 `/api/operator/report` 转发、nested delivery claim 保持 claim、未知字段本机拒绝、Express route 顶层 false。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖高级诊断表单存在、首屏不泄漏工程词、提交 body 不含顶层 `delivery_success/safe_to_control`。
- `docs/product/pc_tools_workstation.md`
  - 更新 Robot Control report submit proxy、body 白名单、fail-closed 和 UI 边界。
- `sprints/2026.06.11_06-20_pc_operator_report_submit/artifacts/`
  - 保存 Browser/DOM smoke 与真实上位机 POST/summary smoke JSON。

## 接口影响

- 新增 workstation API：
  - `POST /api/robot-control/operator/report?baseUrl=<robot-api-base-url>`
  - 固定转发到上位机 `POST /api/operator/report`
  - 不开放任意 endpoint、`/api/base/manual`、`/cmd_vel`、Nav2 goal、map/radar start。
- 新增共享 request/response contract：
  - 允许顶层字段：`operator_present`、`evidence_ref`、`physical_clearance_confirmed`、`emergency_stop_ready`、`observed_motion`、`observed_stop`、`reported_at`、`operator_notes`、`structured_hil_claims`。
  - 允许 nested claim 字段：`external_video_recorded`、`external_video_ref`、`visible_content_proven`、`camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_ref`、`physical_motion_lidar_delta_proven`、`scan_delta_ref`、`real_route_map_proven`、`route_map_ref`、`delivery_success`、`site_state`。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - 输出摘要：`✓ 33 modules transformed`，`✓ built in 1.50s`。
- `cd pc-tools/workstation && npm run test`
  - 通过。
  - 输出摘要：`Test Files 2 passed (2)`，`Tests 86 passed (86)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
- `git diff --check`
  - 通过，无 whitespace error。
- Browser/DOM smoke
  - artifact：`sprints/2026.06.11_06-20_pc_operator_report_submit/artifacts/browser_dom_smoke.json`
  - 关键断言：`.robot-console-grid > .snapshot-panel` 为 5；首屏 forbidden hits 为空；高级诊断打开后存在“现场 HIL 材料”和“提交现场材料（高级）”。
- 真实上位机 smoke
  - artifact：`sprints/2026.06.11_06-20_pc_operator_report_submit/artifacts/operator_report_real_smoke.json`
  - workstation 请求只有：
    - `POST /api/robot-control/operator/report?baseUrl=http://192.168.1.11:8787`
    - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 关键字段：
    - `post.proxy_status=report_forwarded`
    - `post.remote_endpoint=/api/operator/report`
    - `post.delivery_success=false`
    - `post.safe_to_control=false`
    - `post.robot_control_executed=false`
    - `summary.operator_hil_material_summary.evidence_ref=field-hil-20260611-0620-pc-submit-no-motion`
    - `summary.operator_hil_material_summary.site_state=pc_operator_report_no_motion_smoke`
    - `summary_proxy_policy_current=true`
    - `no_workstation_motion_proxy_called=true`

## 剩余风险

- 本轮只提交 no-motion operator report 材料，不证明真实运动、真实 delivery、真实 HIL pass 或真实底盘安全。
- 真实上位机 summary 当前仍因 `/api/status` 内已有 `sends_commands` 类字段被 PC summary 标为 `console_status=blocked`；这不影响本轮 report submit 断言，但后续若要把 summary 变成完全 readable，需要机器人侧继续收敛 status 字段语义或 PC 侧细分传感器 helper 与底盘危险动作。
- 表单当前只提供简洁输入与 checkbox，不做本地文件上传；现场视频、camera artifact、feedback、scan delta、route/map 仍需现场人员提供可追溯 ref。

## 完成前自检

- 未改动 `onboard/**` 或 `docs/vendor/**`。
- 未新增真实运动、底盘、Nav2 goal、map/radar start 代理。
- 未改动普通首屏 `.robot-console-grid` 五张卡和普通动作集合。
- 代码技术注释继续使用中文，新增复杂安全逻辑都有中文原因说明。
- 运行时间记录：2026-06-11 06:24:38 CST。
