# PC Free-Roam Summary 所见即所得字段

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `readback_summary.free_roam` 增加 `start_ready`、`motion_ready`、`mapping_ready`、`mapping_missing`。
  - 字段只读派生自上车端 free-roam runtime/gates，不改变任何发车、stop 或建图行为。
  - `start_ready` 表示自由移动是否可在安全确认后发起；`motion_ready` 表示当前运动发布是否已经解锁；`mapping_ready`/`mapping_missing` 表示是否可按建图验收收口。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步新增 summary 合同字段。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐默认 fixture 的 free-roam summary 字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 free-roam runtime summary 的精确断言，锁住“可自由移动”和“可建图验收”分层。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "free-roam|free roam"`，结果 `7 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`282 passed (282)`。
- 已通过：`git diff --check`
- 已重启：PC Node 通过 `launchctl` 监听 `0.0.0.0:7001`，当前 PID `72846`。
- live 只读摘要：
  - `readback_summary.free_roam.start_ready=true`
  - `motion_ready=false`
  - `mapping_ready=false`
  - `mapping_missing=camera_first_frame,mapping_active,fresh_map_preview`
  - `safe_command_boundary.free_roam_autonomy_start_ready=true`
  - camera 仍是 `source_first_frame_failed / capture_read_returned_false`，共享预览 `exclusive=false`
  - Nav2 仍是 `goal_succeeded_wheel_feedback_not_proven`，下次模式 `ros`，wheel L/R=`0/0`

## 剩余风险

- 本轮没有触发真实小车运动；只让 PC summary 更直接暴露自由移动/建图验收状态。
- 真实 live 已证明自由移动可在安全确认后发起，但运动发布当前尚未解锁；是否实际移动仍需要现场 operator 明确确认后再启动。
- 建图验收仍缺摄像头首帧、地图记录 active 和 fresh map preview。
