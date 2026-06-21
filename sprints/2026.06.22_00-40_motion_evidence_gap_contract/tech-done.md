# 2026-06-22 00:40 Motion Evidence Gap Contract

## sprint_type

micro

## 功能设计

目标：继续推进“能移动 / PC 上连接和控制”的证据闭环。PC first-jog 已经能在缺现场画面时
本机拒绝，且会采集 before/after 固定 GET 快照；但响应里只有一段
`motion_evidence_summary`，不能稳定告诉下一步还缺哪些运动证据。

本轮设计：

- 在 base manual / first-jog / stop 固定代理响应中新增 `motion_evidence_gaps`。
- 对 first-jog/manual：
  - 本机拒绝或远端失败时包含 `motion_command_not_forwarded`。
  - before/after 快照不完整时包含 `before_after_evidence_snapshot_incomplete`。
  - 未看到结构化轮速非零 proof 时包含 `wheel_feedback_lr_nonzero_not_proven`。
  - 未看到结构化 LiDAR motion delta proof 时包含 `physical_motion_lidar_delta_not_proven`。
- 对 stop：
  - 固定返回 `stop_command_not_motion_proof`，避免把停止动作误当移动证据。
- 只读 `T=1001` 反馈仍不算轮速非零证明；它只能证明底盘反馈链路有回包。
- 不新增任何运动命令，不放宽 first-jog preflight。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `BaseCommandEvidenceCapture` 新增 `motion_evidence_gaps`。
  - 新增 gap 推导逻辑，仅当 after readback 出现结构化 proof 字段时才清除对应 gap。
  - failure 响应统一补 `motion_command_not_forwarded`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlBaseCommandProxyResponse` 新增 `motion_evidence_gaps`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级诊断显示 `motion evidence gaps`。
  - 前端 fallback 响应补齐 `motion_evidence_gaps`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 base command fixture。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增本机拒绝时 gap 字段断言。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，19 tests passed。
- `cd pc-tools/workstation && npm run test -- catalog.test.ts`：通过，79 tests passed。
- `cd pc-tools/workstation && npm run test`：通过，98 tests passed。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- 真实 PC proxy 对 `http://192.168.1.11:8787` 的 first-jog 当前拒绝验证：
  - `proxy_status=command_rejected`
  - `failure_reason=first_jog_preflight_required`
  - `remote_http_status=null`
  - `robot_control_executed=false`
  - `missing_fields=["external_video_or_visible_camera"]`
  - `motion_evidence_gaps=["motion_command_not_forwarded","before_after_evidence_snapshot_incomplete","wheel_feedback_lr_nonzero_not_proven","physical_motion_lidar_delta_not_proven"]`
- 关键 artifact：
  - `artifacts/01_pc_first_jog_reject_with_motion_gaps.json`

## 剩余风险

- 本轮没有执行真实运动；first-jog 仍被缺现场画面材料阻断。
- 当前 gap 合同只暴露证据缺口；要真正清除 `wheel_feedback_lr_nonzero_not_proven` 和
  `physical_motion_lidar_delta_not_proven`，还需要后续真实试动后的上位机结构化 proof。
- 地图仍为 `free=0`，不可导航。
