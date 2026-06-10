# PC Nav Goal Preflight Gate

## Sprint 类型与目标

- sprint_type: micro
- 目标：`navigation_goal_preflight_only_no_motion`
- 边界：本轮只实现 PC “定位移动 / 自动寻路”执行前门禁 V1，不执行导航，不调用真实 NavigateToPose、`/api/nav2/start`、`/cmd_vel` 或 `/api/base/manual`。
- Owner：full-stack-software-engineer

## 设计口径

- 新增 workstation 固定代理 `POST /api/robot-control/nav2/goal/preflight?baseUrl=<robot-api-base-url>`。
- 请求体只允许 `goal_frame_id`、`goal_x`、`goal_y`、`goal_yaw`、`confirm_navigation_preflight`；未知字段或非法类型本机拒绝。
- `goal_frame_id` 固定 `map`；`goal_x/goal_y/goal_yaw` 在 Node 端 clamp 到保守范围。
- 代理只读取固定 GET readback：`/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/operator/report`、`/api/nav2/status`。
- 放行条件：定位 reset/runtime 证据、`map_to_base_link` TF、Nav2 path generated 且点数大于 0、operator material preflight passed、显式确认 checkbox。
- 通过也只返回 `ready_for_navigation_goal_not_executed`，顶层固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- PC 普通首屏仍保持五张卡片；目标输入和预检结果只在默认关闭的 `高级诊断 -> Nav2 规划详情`。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `RobotControlNavGoalPreflightRequest/Response` 合同，固定 `robot_control_executed=false` 和禁止执行 endpoint 列表。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `buildNavGoalPreflightProxy()`，做 baseUrl guard、请求体白名单、goal clamp、固定 GET readback、operator report material preflight、缺项汇总和 fail-closed 响应。
- `pc-tools/workstation/src/server/index.ts`、`src/server/catalog.ts`：挂载并导出 `POST /api/robot-control/nav2/goal/preflight?baseUrl=...`。
- `pc-tools/workstation/src/client/workstationApi.ts`：新增前端 client 调用，组件不能拼任意 Robot API endpoint。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在默认关闭的 `高级诊断 -> Nav2 规划详情` 新增“导航目标预检（高级）”表单、确认 checkbox、最近结果、缺失项、readback endpoint 和禁止执行 endpoint 摘要；首屏五张卡片未新增目标输入。
- `pc-tools/workstation/test/App.test.ts`：补首屏禁词、DOM 表单存在、预检提交只命中 workstation endpoint、不触碰执行 endpoint 的 UI 测试。
- `pc-tools/workstation/test/catalog.test.ts`：补 unknown field reject、成功 fixture 也不执行导航、缺 localization/path/operator material reject 的 server 合同测试。
- `docs/product/pc_tools_workstation.md`：新增 `PC Navigation Goal Preflight Gate V1` 产品边界。
- `sprints/2026.06.11_06-55_pc_nav_goal_preflight_gate/artifacts/`：保存 Browser DOM smoke 与真实上位机 no-motion smoke JSON。

## 主节点验收修复

- 修复 `remote_read_endpoints` 泄露内部 `payload`：`buildNavGoalPreflightProxy()` 和 `blockedNavGoalPreflightResponse()` 现在通过 `publicReadbacks()` 把 `InternalRobotApiEndpointReadback[]` 映射为纯 `RobotApiEndpointReadback[]`，只保留 `id/endpoint/http_status/request_status/schema/status/evidence_ref/key_values/blocked_reasons/dangerous_true_fields`。
- 增加测试断言：`JSON.stringify(response.remote_read_endpoints)` 不包含 `"payload"`；Express route 响应同样不包含 `"payload"`。
- 修复真实 smoke artifact 的 no-motion 字段：`no_motion_assertion.robot_control_executed=false`，并新增明确布尔 `response_robot_control_executed_false=true`，避免把 “body 字段为 false 的校验结果” 误读成执行了控制。

## 验证结果

- 重新验证 `cd pc-tools/workstation && npm run test`：通过。`Test Files 2 passed (2)`，`Tests 89 passed (89)`。
- 重新验证 `cd pc-tools/workstation && npm run build`：通过。Vite 输出 `dist/assets/index-CEoVEFXS.js`，server/client TypeScript 均通过。
- 重新验证 `cd pc-tools/workstation && npm run lint`：通过。
- 重新验证 `git diff --check`：通过，无 whitespace error。
- 重新生成 Browser/DOM smoke：通过，artifact 为 `sprints/2026.06.11_06-55_pc_nav_goal_preflight_gate/artifacts/browser_dom_smoke.json`。关键字段：`title=Rober 小车控制台`、`first_screen_card_count=5`、`card_titles=[小车连接, 实时画面, 雷达, 地图, 移动/导航]`、`first_screen_forbidden_hits=[]`、`details_open_default=false`、`advanced_has_nav_goal_preflight=true`、`advanced_has_recent_result=true`。
- 重新生成真实上位机 no-motion smoke：通过 workstation 代理对 `http://192.168.1.11:8787` 发送 goal preflight，artifact 为 `sprints/2026.06.11_06-55_pc_nav_goal_preflight_gate/artifacts/real_upper_nav_goal_preflight_smoke.json`。结果符合预期：HTTP 400、`proxy_status=preflight_rejected`、`preflight_status=preflight_rejected`、`missing_requirements=["operator_report_preflight_required"]`、`remote_methods_used=["GET"]`、readback endpoints 为 `/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/operator/report`、`/api/nav2/status` 且均 loaded 200、`forbidden_remote_endpoints_not_called=["/api/nav2/start","NavigateToPose","/cmd_vel","/api/base/manual"]`、`robot_control_executed=false`、`response_robot_control_executed_false=true`、`remote_read_endpoints_contains_payload=false`，整份 artifact 不包含 `"payload"`。

## 剩余风险

- 本轮没有执行真实导航，也没有触发 NavigateToPose、`/api/nav2/start`、`/cmd_vel` 或 `/api/base/manual`；因此不证明真实自动寻路可用。
- 真实上位机已有 localization/path readback，但 operator material gate 当前仍缺 `operator_report_preflight_required`，后续若要进入真实导航执行，还需要 Robot/Hardware 侧补齐 operator report 材料、导航执行安全边界、取消/停止/恢复 ACK 和受控现场验收。
- 本轮 smoke 证明 workstation 代理和真实上位机 fixed GET readback 可用；不等于 HIL pass、真实路径执行成功或 delivery success。
