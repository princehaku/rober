# Free Roam Natural Aliases

## sprint_type

micro

## 目标

- 修复 `GET /api/robot-control/summary` 顶层 `free_roam_*` 自然命名字段为 `null` 的问题。
- 让现场脚本按 free-roam 命名即可读取自由自助移动的固定 start/stop/latest 和验收链路。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 顶层透出 `free_roam_start_endpoint`、`free_roam_stop_endpoint`、`free_roam_latest_endpoint`。
  - 顶层透出 `free_roam_acceptance_endpoints`、`free_roam_readback_endpoints`、`free_roam_required_success_markers`、`free_roam_missing_evidence`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 summary 顶层 `free_roam_*` alias 类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加 `free_roam_*` 与 `free_move_*` / fixed endpoint 同源断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自由移动自然命名 alias 合同。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 通过：`Test Files 3 passed (3)`、`Tests 428 passed (428)`。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示既有 bundle 大小 warning。
- 重启 PC Node：
  - 通过；`node` 监听 `*:7001`。
- 只读 smoke：
  - `free_roam_start_endpoint=/api/robot-control/free-roam/autonomy/start`。
  - `free_roam_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`。
  - `free_roam_latest_endpoint=/api/robot-control/free-roam/autonomy/latest`。
  - `start_same=true`、`stop_same=true`、`latest_same=true`、`acceptance_same=true`、`readback_same=true`、`markers_same=true`。

## 剩余风险

- 本轮只补 summary 顶层只读 alias，不执行或证明真实自由移动；真实完成仍需现场勾安全确认后启动自由移动，并读取 `/api/robot-control/free-roam/autonomy/latest` 的运动证据。
