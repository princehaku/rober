# 2026.07.01 23:38 PC 现场验收缺失证据清单

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `field_acceptance_packet` 新增平铺缺失证据清单：证据 id、中文标签、所属动作、只读读回端点、读回方法、是否需要先执行运动动作。
  - summary 顶层同步新增 `field_acceptance_missing_evidence_*` 别名，现场 curl 不必钻嵌套对象。
  - `/api/robot-control/base/feedback-samples` 在缺失证据清单中按 POST 读回标注。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 `RobotControlFieldAcceptanceMissingEvidenceItem` 和验收包/summary 字段合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-field-acceptance-packet` 和 `plain-field-acceptance-remaining-actions` DOM 同步暴露缺失证据 id、标签、动作 id、读回端点和主缺口。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 summary 顶层缺失证据清单、主缺口和关键证据读回端点。
- `pc-tools/workstation/test/App.test.ts`
  - 更新默认 Robot Control fixture，并覆盖现场验收卡 DOM 字段。
- `pc-tools/README.md`
  - 记录本轮 no-motion 验收清单合同。

## 验证结果

- 通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 245 passed (245)`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json`
  - `vite build`
  - `tsc -p tsconfig.server.json`
  - Vite 仍提示既有大 chunk warning，本轮未处理拆包。
- 通过：`git diff --check`
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node ... TCP *:7001 (LISTEN)`。
- 通过：只读请求 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 当前真实状态：`status=needs_wheel_rerun`。
  - `field_acceptance_missing_evidence_ids=["same_window_wheel_lr_nonzero","delivery_success","same_hold_window_wheel_lr_nonzero","stop_after_release","free_roam_latest_motion_ready","camera_first_frame","lidar_fresh"]`。
  - `field_acceptance_primary_missing_evidence_id=same_window_wheel_lr_nonzero`。
  - `field_acceptance_primary_missing_evidence_action_id=run_nav2_route`。
  - `field_acceptance_primary_missing_evidence_readback_endpoint=/api/robot-control/base/feedback-samples`。
  - `field_acceptance_missing_evidence_items[0].readback_method=POST`，`requires_motion_before_readback=true`，`requires_safety_confirm_before_motion=true`。
  - `field_acceptance_packet.sends_motion_when_clicked=false`。

## 剩余风险

- 本轮不发送任何运动命令；完整 Nav2 路线执行、PC 键盘连续手控、自由移动和建图启动仍需要 CEO 现场安全确认后再跑实车验收。
- 摄像头首帧和雷达 fresh 仍按上位机当前真实读回为准；本轮只是把缺失证据和复验端点结构化显示出来。
