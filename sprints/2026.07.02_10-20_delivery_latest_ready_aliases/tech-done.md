# 2026.07.02 10:20 delivery latest ready aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlDeliveryLatestResponse` 新增 `delivery_claim_ready` 和 `delivery_material_ready`。
- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/delivery/latest` 的 fallback 和真实回包都返回上述字段；`delivery_claim_ready` 跟随 delivery success，`delivery_material_ready` 跟随 `missing_required_material.length === 0`。
- `pc-tools/workstation/test/catalog.test.ts`：补 delivery latest blocked-material 场景断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步 delivery latest ready alias 口径。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 files passed，427 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单 chunk 超 500 kB 的既有警告。
- 重启 PC Node：`0.0.0.0:7001` 已监听，PID `55998`。
- 实机只读 smoke：
  - `GET /api/robot-control/delivery/latest?baseUrl=http://192.168.1.11:8787` 返回 `delivery_success=false`、`delivery_claim_ready=false`、`delivery_material_ready=false`、缺项 `confirm_delivery_completion/operator_report_ready_for_review/operator_observed_motion/operator_observed_stop/structured_hil_claims.delivery_success`。
  - `GET /api/robot-control/summary` 仍为 `status=needs_wheel_rerun`，`trip_execution_missing_evidence=["same_window_wheel_lr_nonzero","delivery_success"]`。

## 剩余风险

- 本轮只增强 delivery latest 读回可见性，不提交送达、不伪造 delivery success。
- 完整 motion 目标仍需显式安全确认后的同窗口 wheel raw L/R 非零、真实送达确认、键盘连续控制和自由移动运行读回。
- WYSIWYG/mapping 仍卡相机首帧：`live_wysiwyg_missing_reasons=["camera"]`，`mapping_start_missing_evidence=["camera_first_frame"]`。
- 未发送任何运动/control POST，未启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，未提交 delivery 或 stop。
