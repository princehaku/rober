# 雷达刷新后同步 status 回读

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `refreshRadarProof()` 在固定 `/api/robot-control/radar/scan-proof/refresh` 完成后，立即再读一次固定 `/api/robot-control/radar/status`。
  - 这样雷达刷新按钮能同步更新地图 marker 和自动扫图 readiness，避免 proof refresh 响应里的短暂旧 readback 让地图继续显示 stale。
  - status 读取失败时写入 fail-closed fallback，不影响地图/summary 其他只读显示。
- `pc-tools/workstation/test/App.test.ts`
  - 增加断言：点击“刷新雷达”后必须请求 `/api/robot-control/radar/status`，并用 fresh status 把地图 marker 恢复到“雷达已运行”。

## 验证结果

- `npm test`：通过，2 个 test files，220 个 tests passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB 的既有 warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 真机只读/固定 refresh smoke：通过。
  - refresh 前 `radar/status` 为 `continuous_scan_status=latest_proof_stale_while_lifecycle_running`、`latest_scan_proof_fresh=false`。
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、`robot_control_executed=false`。
  - refresh 响应内 `latest_readback` 短暂仍显示 stale；随后立即 `GET /api/robot-control/radar/status` 返回 `continuous_scan_status=latest_proof_fresh_while_lifecycle_running`、`latest_scan_proof_fresh=true`、`robot_control_executed=false`。

## 剩余风险

- 雷达 proof refresh 的响应体自身仍可能短暂带旧 readback；PC 已用后续 status 回读兜住 UI，但上位机响应口径后续仍可继续收敛。
- 本轮未触发底盘运动，未推进 Nav2 新行程或 delivery success。
