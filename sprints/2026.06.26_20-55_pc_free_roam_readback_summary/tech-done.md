# PC free-roam readback 摘要

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse.readback_summary` 新增 `free_roam` 短摘要字段，包含 runtime、decision、stop、artifact-only、cmd_vel 发布和 gate 数量。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `freeRoamSummaryFromReadbacks()`，从固定 `/api/free-roam/autonomy/latest` 或旧 `/api/status.free_roam_autonomy` 聚合中读取自动扫图 runtime artifact，并保持 fail-closed 只读语义。
- `pc-tools/workstation/test/catalog.test.ts`：补充回归断言，覆盖 latest 缺失时 `free_roam` 摘要为 not_loaded/0，以及 latest loaded 时能直接读到 `turning_for_coverage`、reason、stop、artifact-only、cmd_vel 和 gate_count。
- `docs/product/pc_tools_workstation.md`：同步记录 PC 工作站最新口径和现场读数。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，105 tests。
- `cd pc-tools/workstation && npm run build`：通过；仅 Vite chunk size warning。
- 变更前现场 PC 7001 summary 中 `readback_summary.free_roam=null`，只能从 `safe_command_boundary.free_roam_autonomy_runtime` 间接读取。
- 当前现场 PC 7001 summary 已可直接读取 `readback_summary.free_roam`：`status=not_proven`、`runtime_status=loaded`、`decision_state=stopping`、`decision_reason=现场请求停止`、`stop_required=true`、`artifact_only=true`、`cmd_vel_publish_enabled=false`、`gate_count=5`。

## 剩余风险

- 本轮只提升自动扫图/free-roam 的只读摘要，不解锁自动运动；`cmd_vel_publish_enabled=false` 仍表示上车端自由移动状态机没有发布运动。
- 完整“自由自助移动并建图”仍需要相机首帧 ready、地图/雷达画面所见即所得、上车端 motion unlock 和现场 stop 兜底验证共同成立。
- 真实相机仍处于 `/dev/video1` 可打开但 `capture.read()` 超时，建图前置画面尚未满足。
