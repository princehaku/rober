# Delivery gap recompute

## sprint_type

micro

## 实际改动

- PC workstation 新增固定 `POST /api/robot-control/delivery/check?baseUrl=...`。
- 该入口转发到上位机 `/api/delivery/complete`，但 body 由 PC 后端写死为 `confirm_delivery_completion=false`、`delivery_evidence_ref=delivery-gap-check-not-confirmed`，浏览器 body 被忽略。
- 高级诊断新增“复算送达缺口（高级）”，用于让上位机用当前 Nav2 latest 与 operator report latest 重新生成 blocked 缺项。
- 新增 `RobotControlDeliveryGapCheckResponse` 合同、client API、Vue pending/result 展示。
- 单测覆盖：
  - server 端确认浏览器传入 `confirm_delivery_completion=true` 也不会透传；
  - UI 端确认按钮只调用 `/api/robot-control/delivery/check`，不会调用 `/api/robot-control/delivery/complete`。
- `docs/product/pc_tools_workstation.md` 同步记录固定 confirm=false 和危险字段边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`108 passed (108)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：`POST /api/robot-control/delivery/check?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`proxy_status=check_loaded`，`remote_http_status=200`。
- smoke 特意发送浏览器 body `confirm_delivery_completion=true` 和 `delivery_success=true`，PC 响应中的实际 `request_body.confirm_delivery_completion=false`、`delivery_evidence_ref=delivery-gap-check-not-confirmed`，证明浏览器无法把 check 入口变成确认送达。
- 真实结果仍 fail-closed：`delivery_success=false`，`robot_control_executed=false`，`delivery_key_values.status=blocked_missing_delivery_material`，`nav2_status=goal_succeeded`，`operator_report_status=unsafe_or_incomplete`，`operator_evidence_ref=delivery-draft-smoke-1782102952`。
- `blocked_reasons` 直出当前缺项：`confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`。

## 剩余风险

- 本轮不证明 delivery success；check 入口刻意固定 confirm=false。
- 若 operator report 仍是草稿或未确认，复算后的 delivery gate 必须保持 blocked。
