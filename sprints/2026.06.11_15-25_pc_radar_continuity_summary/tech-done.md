# 2026.06.11 15:25 PC Radar Continuity Summary

## sprint_type

micro

## 本轮功能点设计

- 目标：让 PC workstation 消费真实上位机 `GET /api/radar/status` 新增的 lifecycle / continuity 字段，让普通用户首屏的“雷达”卡片能表达“雷达已运行且本窗口已看到新鲜观测”，同时不把工程词放回首屏。
- 生产者：真实上位机 `GET /api/radar/status` 与 `POST /api/radar/scan-proof/refresh`。本轮不改 `onboard/**`，只消费既有合同。
- 消费者：
  - `pc-tools/workstation/src/server/robotControlSummary.ts` 把 `radar_status` 里的 lifecycle / continuity 字段压到 `readback_summary.lidar` 和 refresh `latest_readback_key_values`。
  - `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 只在普通用户首屏雷达卡使用短中文结论；高级细节继续留在默认关闭的 `<details>`。
- 字段映射：
  - `continuous_scan_status`
  - `continuous_window_observed`
  - `continuity_window_status`
  - `continuity_blocked_reasons`
  - `lifecycle_running`
  - `lifecycle_state`
  - `latest_scan_proof_fresh`
- 首屏文案边界：
  - 仅允许普通中文短句，例如“雷达已运行”“雷达未运行”“刷新中”“刷新失败”。
  - 禁止在普通首屏出现 `proof`、`HIL`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`O6`、`O7`、`Mock`、`field manifest`。
  - 不新增首屏按钮；仍只保留“刷新雷达”。
- fail-closed 规则：
  - 若 `lifecycle_running !== true`，首屏不能暗示雷达已运行。
  - 若连续窗口未观察到 fresh 观测，只能显示“雷达未运行”或“刷新失败”，不能把旧 collector blocker 误报成当前最终状态。
  - 即使 lifecycle / continuity 全部满足，仍保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 验收命令：
  1. `cd pc-tools/workstation && npm run build`
  2. `cd pc-tools/workstation && npm run test -- --run`
  3. `cd pc-tools/workstation && npm run lint`
  4. `git diff --check`
  5. 真实 PC / 上位机 smoke：起本机 workstation API 临时端口，调用真实上位机 `http://192.168.1.11:8787` 的 radar start / refresh / summary / stop，保存 artifacts，并确认没有触碰 `/dev/ttyS5`、无运动字段 true。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 `readback_summary.lidar` 补齐 `continuous_scan_status`、`lifecycle_running`、
    `lifecycle_state`、`continuous_window_observed`、
    `continuity_window_status`、`latest_scan_proof_fresh` 六个兼容字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `radarScanProofReadbackPayload()` 现在优先消费 refresh 回包里最终
    `upper_api.radar_status.payload` 的 lifecycle / continuity 结论，不再把旧 collector
    blocker 误当成最终状态。
  - 新增 `lidarSummaryFromReadbacks()`，把 `GET /api/radar/status` 的 lifecycle /
    continuity 字段压进 `readback_summary.lidar`。
  - radar refresh key whitelist 新增 continuity / lifecycle 字段，确保 PC refresh response
    能直接带回这些 key values。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `summarizeRadarState()`，普通首屏雷达卡改为消费 summary 的最终雷达结论。
  - 首屏雷达卡只显示 `雷达已运行 / 雷达未运行 / 刷新中 / 刷新失败`，不显示字段名、
    `proof`、`HIL`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、
    `启动雷达`、`停止雷达`。
  - 高级诊断保留 continuity / lifecycle key values 和 summary 压缩串。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 `buildRobotControlSummary()` 会把 radar status 的 continuity / lifecycle 字段压到
    `readback_summary.lidar`。
  - 覆盖 radar refresh proxy 在旧 collector `blocked_reasons` 仍存在时，优先取最终
    `upper_api.radar_status.payload` 的 continuity / lifecycle 字段，而不是旧 blocker。
- `pc-tools/workstation/test/App.test.ts`
  - DOM smoke artifact 路径改到本轮 sprint：`sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/`。
  - 恢复误写的旧 artifact
    `sprints/2026.06.11_11-25_pc_nav2_proof_30s_budget/artifacts/pc_plain_user_home_dom_smoke.json`
    到 `HEAD` 状态，避免污染历史证据。
  - UI 测试改为断言普通首屏雷达卡显示 `雷达已运行`，并继续断言首屏不出现
    `proof`、`HIL`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、
    `启动雷达`、`停止雷达`。
- `docs/product/pc_tools_workstation.md`
  - 记录首屏雷达卡已消费 summary continuity / lifecycle 字段，以及普通用户文案边界。
- `pc-tools/README.md`
  - 记录 workstation 侧已消费 radar continuity / lifecycle 字段，并强调工程词仍只在高级诊断。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - 关键输出：`vite v7.3.3 building client environment for production...`，
    `✓ built in 4.39s`。
- `cd pc-tools/workstation && npm run test -- --run`
  - 通过。
  - 关键输出：`Test Files  2 passed (2)`，`Tests  89 passed (89)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过，无输出。
- `git diff --check`
  - 通过，无输出。
- 普通首屏 DOM smoke
  - artifact：`sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/pc_plain_user_home_dom_smoke.json`
  - 结果：首屏标题仍是 `Rober 小车控制台`，卡片仍只有 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。
  - `forbidden_token_presence` 全部为 `false`，其中包含 `HIL`、`Nav2`、`proof`、
    `/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`。
  - 额外由 `App.test.ts` 断言普通首屏不出现 `启动雷达`、`停止雷达`。
- 真实 PC / 上位机 smoke
  - 本机 workstation API：`http://127.0.0.1:18792`
  - 真实上位机：`http://192.168.1.11:8787`
  - 执行顺序：
    1. `POST /api/robot-control/radar/start`
    2. `POST /api/robot-control/radar/scan-proof/refresh`
    3. `GET /api/robot-control/summary`
    4. `POST /api/robot-control/radar/stop`
    5. 二次 `stop` + 等待 70s 后再次读取 summary 与 cleanup
  - 关键 artifact：
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/radar_start_response.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/radar_refresh_response.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/workstation_summary_after_stop_wait.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/live_smoke_final_summary.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/remote_ttyS5_before.log`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/remote_cleanup.log`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/remote_cleanup_after_wait.log`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke/remote_cleanup_final.log`
  - refresh response 已包含新 continuity / lifecycle key values：
    - `continuous_scan_status=latest_proof_present_but_lifecycle_not_running`
    - `continuous_window_observed=false`
    - `continuity_window_status=latest_proof_present_but_lifecycle_not_running`
    - `lifecycle_running=false`
    - `lifecycle_state=stopped`
    - `latest_scan_proof_fresh=true`
    - `continuity_blocked_reasons=lidar_lifecycle_not_running`
  - workstation summary `readback_summary.lidar` 也已消费这些字段：
    - `continuous_scan_status=latest_proof_present_but_lifecycle_not_running`
    - `lifecycle_running=false`
    - `lifecycle_state=stopped`
    - `continuous_window_observed=false`
    - `continuity_window_status=latest_proof_present_but_lifecycle_not_running`
    - `latest_scan_proof_fresh=true`
  - stop cleanup：
    - 两次 stop 都返回 `proxy_status=lifecycle_forwarded`、`remote_http_status=200`。
    - `remote_ttyS5_before.log`、`remote_cleanup.log`、`remote_cleanup_after_wait.log`、
      `remote_cleanup_final.log` 全部显示 `/dev/ttyS5` 的 `lsof` / `fuser` 为空，确认本轮未占用 / 未触碰 `/dev/ttyS5`。
    - 最终 `remote_cleanup_final.log` 里 `radar helpers` 为空，说明 cleanup 已收口。
  - 危险运动字段：
    - refresh / start / stop proxy 顶层都保持 `safe_to_control=false`、
      `delivery_success=false`、`primary_actions_enabled=false`、
      `robot_control_executed=false`。
    - summary 顶层这四个字段也保持 `false`。
- supplemental running-window smoke
  - 本机 workstation API：`http://127.0.0.1:18793`
  - 真实上位机：`http://192.168.1.11:8787`
  - 执行顺序严格按验收要求：
    1. PC proxy `POST /api/robot-control/radar/start`
    2. direct upper `POST /api/radar/scan-proof/refresh`，body
       `{"timeout_s":12,"runtime_warmup_s":0,"start_runtime":false}`
    3. PC `GET /api/robot-control/summary`
    4. PC proxy `POST /api/robot-control/radar/stop`
    5. 等待 70s 后做 cleanup 检查
  - artifact 目录：
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/pc_radar_start.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/direct_upper_refresh.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/pc_summary_after_direct_refresh.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/pc_radar_stop.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/running_window_summary.json`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/remote_devices_before.log`
    - `sprints/2026.06.11_15-25_pc_radar_continuity_summary/artifacts/live_smoke_running_window/remote_cleanup_after_stop.log`
  - direct upper refresh 本身仍是 collector 结果回包，顶层没有直接回显 continuity / lifecycle 字段；但它成功生成 fresh proof，`evidence_ref=o1-lidar-scan-proof-1781163720952`，且顶层继续保持
    `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
    `robot_control_executed=false`。
  - 关键验收结果在 PC summary：
    - `continuous_scan_status=latest_proof_fresh_while_lifecycle_running`
    - `lifecycle_running=true`
    - `lifecycle_state=running`
    - `continuous_window_observed=true`
    - `continuity_window_status=latest_proof_fresh_while_lifecycle_running`
    - `latest_scan_proof_fresh=true`
  - cleanup：
    - `remote_cleanup_after_stop.log` 显示 `/dev/ttyACM0`、`/dev/ttyS5` 的 `lsof` / `fuser`
      都为空。
    - `helpers after` 为空，说明 stop 后无 LiDAR lifecycle / collector / driver /
      static TF 残留。
  - 危险运动字段：
    - `pc_radar_start.json`、`pc_radar_stop.json` 顶层仍是
      `safe_to_control=false`、`delivery_success=false`、
      `primary_actions_enabled=false`、`robot_control_executed=false`。
    - `pc_summary_after_direct_refresh.json` 顶层也保持
      `safe_to_control=false`、`delivery_success=false`、
      `primary_actions_enabled=false`；`robot_control_executed` 未被置 true。

## 剩余风险

- supplemental running-window smoke 已经复现真实
  `lifecycle_running=true + continuous_window_observed=true + latest_scan_proof_fresh=true`
  的窗口，因此“PC summary 能显示 running + observed”这一现场证据缺口已关闭。
- `GET /api/robot-control/summary` 在第一次 refresh 后立即读取时，真实上位机部分只读端点会超时；
  stop 后等待再读 summary 才稳定得到 continuity / lifecycle 字段。当前 PC 已能消费字段，
  但真实板端即时读窗口仍受上位机时序影响。
- summary 的 `robot_api_connection.dangerous_true_fields` 仍会看到
  `status.base.feedback_readback.sends_commands` / `status.base.sends_commands`，这是既有
  base status 合同行为，不是本轮新引入问题；本轮没有改 `onboard/**`，因此只保留为已知风险。
