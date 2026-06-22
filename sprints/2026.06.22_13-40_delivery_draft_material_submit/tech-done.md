# Delivery draft material submit

## sprint_type

micro

## 实际改动

- PC 高级诊断送达材料表单新增“提交送达草稿（高级）”。
- 草稿只提交固定 `/api/robot-control/operator/report`，保存已预填的 visual ref 和 route/map ref。
- 草稿明确写入 `operator_present=false`、`physical_clearance_confirmed=false`、`emergency_stop_ready=false`、`observed_motion=false`、`observed_stop=false`、`structured_hil_claims.delivery_success=false` 和 `site_state=delivery_material_draft_not_operator_confirmed`。
- 草稿提交后刷新 PC summary / readback，用于把 operator report 404 缺口推进为“有草稿材料但缺现场确认”的可复核状态；`/api/delivery/latest` 仍是上位机最近一次 delivery gate artifact，只有显式跑 delivery gate 后才会重新合成。
- `pc-tools/workstation/test/App.test.ts` 增加回归，确认草稿不会调用 `/api/robot-control/delivery/complete`，也不会把顶层 `delivery_success` 写入 body。
- `docs/product/pc_tools_workstation.md` 同步记录草稿入口和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`106 passed (106)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：先读取真实 Nav2 latest `evidence_ref=o11-nav2-goal-execution-1782099547218`，再通过 camera first-frame probe 生成 `sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782102949377.jpg`，随后提交草稿 operator report。
- 草稿 POST 结果：HTTP 200，`proxy_status=report_forwarded`，`remote_http_status=200`，`status=loaded_fail_closed_summary`，`delivery_success=false`，`robot_control_executed=false`，请求体中 `structured_hil_claims.delivery_success=false`、`observed_motion=false`。
- 真实 PC summary 复验：`operator_hil_material_summary.status=loaded`，`report_status=unsafe_or_incomplete`，`evidence_ref=delivery-draft-smoke-1782102952`，`external_video=true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_1782102949377.jpg`，`camera_visible=true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_1782102949377.jpg`，`route_map=true; ref=o11-nav2-goal-execution-1782099547218`，`delivery_claim=false`，`site_state=delivery_material_draft_not_operator_confirmed`。
- `GET /api/delivery/latest` 仍保持 `delivery_success=false`；这是预期，因为草稿没有现场确认，也没有触发 delivery gate 合成。

## 剩余风险

- 本轮不证明 delivery success；草稿 deliberately 不包含现场确认。
- delivery success 仍必须由现场 operator 显式确认 observed motion/stop 和 delivery claim 后，再通过 delivery gate 给出。
