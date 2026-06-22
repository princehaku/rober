# Delivery latest gap panel

## sprint_type

micro

## 实际改动

- PC workstation 新增固定只读代理 `GET /api/robot-control/delivery/latest?baseUrl=...`，只转发到上位机 `GET /api/delivery/latest`。
- 高级诊断新增“读取送达缺口（高级）”，显示 delivery gate 最近状态、缺失材料、Nav2 子状态和 operator report 子状态。
- `deliveryCompleteKeyValues` 同时支持 `/api/delivery/complete` POST 响应和 `/api/delivery/latest` 的 `latest_result` 结构。
- 单测覆盖 delivery latest 只读行为：只 GET `/api/delivery/latest`，不提交 `/api/delivery/complete`、`/api/operator/report`、`/api/base/manual`。
- `docs/product/pc_tools_workstation.md` 同步记录只读缺口面板和 fail-closed 边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`102 passed (102)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：`GET /api/robot-control/delivery/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`proxy_status=latest_loaded`，`status=loaded_fail_closed_summary`，`proof_status=not_proven`，`delivery_success=false`，`robot_control_executed=false`，`hard_dangerous_true_fields=[]`。
- 同一真实 smoke 的 `delivery_key_values` 显示 `status=blocked_missing_delivery_material`、`nav2_status=goal_succeeded`、`nav2_result_status=succeeded`、`nav2_feedback_sample_count=8`；`blocked_reasons` 精确列出 8 个缺项：`operator_report_latest_http_200`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`、`structured_hil_claims.real_route_map_proven`、`structured_hil_claims.route_map_ref`、`external_video_or_visible_camera_ref`。

## 剩余风险

- 本轮不伪造 delivery success；只把上位机 delivery gate 缺项在 PC 高级诊断里展示清楚。
- 当前真实送达仍依赖现场 operator report、observed motion/stop、外部视频或可见相机 ref、route/map ref 和 delivery claim。
- 普通首屏继续保持简易风格；工程字段仍只在默认关闭的高级诊断中。
