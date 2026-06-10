# PC Structured HIL Report Readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：给 Robot Control summary 增加 `operator_hil_material_summary` 合同。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 `/api/operator/report` 的 `structured_hil_claims` 生成高级诊断摘要，并把 `structured_hil_claims.delivery_success=true` 限定为人工材料 claim；其它非 claim 路径上的危险 true 字段继续 blocked。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在默认关闭的 `高级诊断` 新增“现场 HIL 材料”小节；普通首屏布局、五张卡片和普通动作集合未改。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补 summary 行为、危险字段扫描和首屏/高级诊断渲染断言。
- `docs/product/pc_tools_workstation.md`：同步记录结构化 HIL report readback 边界。

## 验证结果

- 2026-06-11 06:07 复验修正：
  - 收紧 `structured_hil_claims.delivery_success=true` 豁免范围：默认危险字段扫描不豁免，只有 `operator_report_latest` endpoint 的精确 operator report claim 路径不 hard-block。
  - 修正 `operator_hil_material_summary.report_status`：先递归读取 `operator_report_status`，再兜底 `status`，可消费真实上位机 `latest_result.operator_report_status`。
  - 测试新增/更新覆盖：
    - `operator_report_latest` 顶层、`latest_result.structured_hil_claims`、`latest_result.operator_report.structured_hil_claims` 的 delivery claim 不 hard-block。
    - 其它 endpoint 中伪造 `structured_hil_claims.delivery_success=true` 仍 hard-block。
    - 非 claim 路径 `delivery_success=true` 与 `hil_pass=true` 仍 hard-block。
- 已通过定向验证：`cd pc-tools/workstation && npm run test -- --run test/catalog.test.ts test/App.test.ts`，结果 `2 passed (2)`、`82 passed (82)`。
- 已通过构建：`cd pc-tools/workstation && npm run build`，结果 `tsc` 与 `vite build` 成功（06:07 复跑通过）。
- 已通过完整测试：`cd pc-tools/workstation && npm run test`，结果 `2 passed (2)`、`82 passed (82)`（06:07 复跑通过）。
- 已通过 lint：`cd pc-tools/workstation && npm run lint`，结果 `eslint .` 无报错（06:07 复跑通过）。
- 已通过 diff 检查：`git diff --check` 无输出（06:07 复跑通过）。
- Browser/DOM smoke：启动本地 workstation API `http://127.0.0.1:8787` 和 Vite `http://127.0.0.1:5173`，用只读 mock Robot API `http://127.0.0.1:8791` 验证页面。结果保存在 `artifacts/browser_smoke_robot_control_structured_hil.json`：
  - `.robot-console-grid > .snapshot-panel` 为 5 张卡。
  - 首屏标题为 `Rober 小车控制台`。
  - 首屏卡片为 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。
  - 首屏动作只出现 `连接/刷新 / 打开画面 / 关闭画面 / 刷新雷达 / 刷新地图 / 地图列表 / 检查路径 / 停止`。
  - 首屏禁词 `HIL`、`delivery_success`、`structured_hil_claims`、`轮速反馈`、`外部视频`、`safe_to_control`、`/cmd_vel`、`/api/base/manual` 均未命中。
  - 展开 `高级诊断` 后可见 `现场 HIL 材料`、`operator_report_latest.structured_hil_claims`、外部视频、轮速反馈、delivery claim、site_state 和 report status。
- Browser screenshot：in-app Browser `tab.screenshot()` 连续两次在 `Page.captureScreenshot` 超时，且该线程不支持切换 Browser 可见模式，所以本轮只保存 DOM smoke JSON，没有可用 PNG 截图。
- 真实上位机 PC summary smoke：只通过 workstation Node proxy 执行 GET：
  `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`。
  完整 JSON 已在 06:08 复写到 `artifacts/real_board_robot_control_summary_192_168_1_11_8787.json`，关键字段：
  - `operator_report_latest.http_status=200`
  - `operator_report_latest.request_status=loaded`
  - `operator_report_latest.dangerous_true_fields=[]`
  - `operator_hil_material_summary.status=loaded`
  - `operator_hil_material_summary.report_status=ready_for_execution`
  - `operator_hil_material_summary.delivery_claim=true`
  - `operator_hil_material_summary.evidence_ref=field-hil-20260611-0545-structured-report-smoke`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `safe_command_boundary.robot_control_executed=false`
  - `operator_report_latest` 内部 claim 路径未进入 dangerous；其它 endpoint 的 `status.operator_report.structured_hil_claims.delivery_success` 仍按非 operator_report_latest endpoint 语义 hard-block。

## 剩余风险

- 本轮只读消费 `/api/operator/report`，不发送任何运动命令，不证明 HIL pass、真实 delivery、真实 safe control 或底盘可控。
- 真实上位机 smoke 只允许 GET summary/readback；本轮没有调用 `/api/base/manual`、`/cmd_vel`、Nav2 goal 或任何运动命令。
- 真实 summary 仍因 `status.base.feedback_readback.sends_commands`、`status.base.sends_commands` 和 base readback timeout 保持 `console_status=blocked`，这是 fail-closed 状态，不影响本轮 operator report claim 旁路验证。
- Browser 截图 artifact 缺失是工具截图能力限制；DOM smoke JSON 已覆盖首屏卡片、首屏禁词和高级诊断结构化 HIL 材料可见性。
