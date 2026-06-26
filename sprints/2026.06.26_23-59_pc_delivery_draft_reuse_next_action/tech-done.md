# 2026.06.26 23:59 PC 送达草稿复用下一步提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当普通首屏已从 latest 恢复 `delivery_material_draft_not_operator_confirmed` 草稿、但当前 Nav2 行程还不能用于本轮送达时，`下一步` 文案增加 `送达材料草稿已保存，可复用；` 前缀。
  - 该前缀只作用于行程未就绪分支；不改变 `delivery_success`、operator report、delivery complete 或任何运动控制 gate。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 latest 草稿恢复用例，锁定 `plain-delivery-next-action` 和本轮进度都显示草稿可复用。
  - 同一用例继续断言不会调用 `/api/robot-control/operator/report`、`/api/robot-control/delivery/complete`、Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录送达草稿复用下一步提示的产品口径和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "prefills plain delivery material refs"`：1 passed，118 skipped。
- `npm test -- test/App.test.ts`：119 passed。
- `npm test`：2 files passed，215 tests passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB，这是既有打包提示。
- `npm run lint`：通过。
- `git diff --check`：通过。
- Live 7001 重启验证：`npm run api` 输出 `pc-tools workstation API listening on http://0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
- Live 上位机只读验证：
  - `GET http://127.0.0.1:7001/api/robot-control/delivery/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `proxy_status=latest_loaded`、`delivery_success=false`、`status=blocked_missing_delivery_material`。
  - latest 仍带 `delivery_material_refs.site_state=delivery_material_draft_not_operator_confirmed`，并保留 `operator_evidence_ref=delivery-draft-smoke-1782102952`、相机样张 ref 与 route map ref。
  - blocked/missing 仍包含 `confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`。
  - `GET /api/robot-control/summary` 返回 `source_base_url=http://192.168.1.11:8787`、Robot API `readable`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，free roam 仍为 `locked/artifact_only=true/cmd_vel_publish_enabled=false`。

## 剩余风险

- 本轮只改善送达草稿复用提示，不宣称送达成功。
- 当前 live 证据仍显示 wheel raw L/R 为 `0/0` 且 `wheel_feedback_lr_nonzero_proven=false`；还需要真实低速试动读到非零 L/R。
- 完整 Nav2 路线执行仍只有旧 `goal_succeeded + feedback_sample_count=8` 草稿材料，当前 delivery gate 仍要求重新执行/读取本轮行程并完成人工确认。
- PC 键盘连续手控、delivery success、自动扫地式建图真车自由跑动仍未完成 HIL 验证。
