# Full-stack Owner Note

## sprint_type

epic owner note for `2026.06.04_22-23_runtime-material-deploy-refresh`.

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 direct-upper command response 增加 `upper_result_summary`，把上位机 HTTP 转发结果和业务 proof 结果拆开。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`：`radar_scan_proof_refresh` 从 upper body 摘取 `status`、`proof_status`、`latest_proof_status`、artifact、freshness、blockers、not_proven 和固定安全字段；HTTP 2xx 但 upper 仍 `not_proven` 时保持 `fail_closed=true`。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`：Refresh scan proof 按钮结果显示 `upper_result=...`、`upper_blockers=...`、artifact/freshness 摘要，并用“已触发但 upper 仍 not_proven（仍锁定）”避免 operator 误读为 runtime success。
- `pc-tools/workstation/test/App.test.ts`：增加 HTTP 200 + upper `status=not_proven` / `ros2_command_unavailable` / `upper_api_scan_not_proven` 的 API 和 UI 回归覆盖。
- `docs/interfaces/o7_direct_upper_pc_api.md`、`docs/product/pc_tools_workstation.md`：同步 direct-upper refresh command response 口径和 O7 不涨分边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run`
  - Result: pass
  - Evidence: `Test Files 3 passed (3)`、`Tests 101 passed (101)`、`Duration 18.96s`

## 未做 live smoke

- 本轮按 CEO 指令不做 live smoke。
- 未调用 `/api/base/manual`、`/cmd_vel` 或任何底盘/运动命令。
- 未调用真实上位机 `POST /api/radar/scan-proof/refresh`；本 note 只记录 PC API/UI 对 2xx + `not_proven` payload 的软件护栏。

## O7 涨分边界

- O7 不涨分。
- 本轮只证明 PC direct-upper refresh command response 能显式暴露 upper `not_proven` 和 blockers，不证明 fresh `/scan`、SLAM/map、Nav2 消费、PC WASD 现场控车、ACK/T=1001、HIL、`safe_to_control=true` 或 delivery success。

## 剩余风险

- 仍需 Robot Software/现场链路提供 deployed upper fresh runtime 材料，特别是 `/scan` once+hz、collector log、latest artifact 和 `safe_to_control=false` 边界。
- 如果 upper 继续返回 `ros2_command_unavailable` / `upper_api_scan_not_proven`，PC 现在会如实展示 blocker；该 blocker 本身仍需要 ROS2 runtime owner 处理。
