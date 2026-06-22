# Nav2 latest delivery prefill

## sprint_type

micro

## 实际改动

- `pc-tools/workstation` 新增固定只读代理 `GET /api/robot-control/nav2/goal/execution/latest?baseUrl=...`，只转发到上位机 `GET /api/nav2/goal/execution/latest`，不重新执行 NavigateToPose、不调用 base manual 或 cmd_vel。
- PC 高级诊断新增“读取最近 Nav2 结果（高级）”，页面刷新后也能读取最近 Nav2 artifact `evidence_ref`。
- “使用最近 Nav2 ref” 同时支持刚执行的 Nav2 goal 结果和上位机 latest 结果，用于预填送达 operator report 的 `route_map_ref` 与 `delivery_evidence_ref`。
- `navGoalExecutionKeyValues` 改为优先读取上位机 `latest_result`，避免真实 latest 响应顶层 `status` 覆盖 action artifact 的 `goal_succeeded`。
- `docs/product/pc_tools_workstation.md` 同步记录 latest fixed GET、UI 行为和 fail-closed 边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`101 passed (101)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：`GET /api/robot-control/nav2/goal/execution/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`proxy_status=latest_loaded`，`evidence_ref=o11-nav2-goal-execution-1782099547218`，`goal_status=goal_succeeded`，`result_status=succeeded`，`feedback_sample_count=8`，`delivery_success=false`，`robot_control_executed=false`，`hard_dangerous_true_fields=[]`。
- 真实上位机 `GET /api/delivery/latest` 返回 HTTP 200，顶层 `delivery_success=false`；`latest_result.nav2_goal_execution.status=goal_succeeded` 已满足，但 `latest_result.status=blocked_missing_delivery_material`，缺 `operator_report_latest_http_200`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`、`structured_hil_claims.real_route_map_proven`、`structured_hil_claims.route_map_ref`、`external_video_or_visible_camera_ref`。

## 剩余风险

- 本轮只提升 PC 送达材料预填和 latest 证据读取易用性；不伪造 delivery success。
- 当前真实 delivery gate 仍依赖现场 operator report、送达视频、observed motion/stop、route/map ref 等材料补齐。
- `delivery_success=true` 必须由上位机 delivery gate 在真实材料齐备后给出；PC latest 只读入口不会把 Nav2 succeeded 外推为送达成功。
