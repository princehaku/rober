# PC Radar Cold Start Refresh Stabilization Tech Done

## Sprint Type

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 PC workstation 固定雷达 scan-proof refresh body 调整为
    `{"timeout_s":20,"runtime_warmup_s":15,"start_runtime":true}`。
  - PC fetch timeout 随固定 body 自动计算为 `45000ms`。
  - 修复 radar refresh 摘要选择：当上位机 refresh 回包同时包含直接 collector 结果和
    `upper_api.radar_status.latest_scan_proof` readback 时，优先展示最终 radar status/latest
    scan proof 的四项观测字段，避免冷启动竞态把旧的 false 摘要显示到 PC 页面。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新固定 body、timeout budget 和 hang timeout 断言。
  - 新增 direct false 但 radar status latest true 的代理摘要回归测试。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC Radar/Map Proof Refresh V2 的固定 body 和冷启动 no-motion 边界。
- `pc-tools/README.md`
  - 同步普通 workstation 使用说明中的固定 radar refresh body。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 新增 2026-06-11 PC radar cold-start refresh 稳定化记录。
- `sprints/2026.06.11_10-50_pc_radar_cold_start_refresh_stabilization/artifacts/`
  - 保存 PC proxy、upper latest/readback、stop/cleanup 和失败定位 artifact。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 完成，TypeScript client/server 编译通过。
- `cd pc-tools/workstation && npm run test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 89 passed (89)`。
  - `.simple-user-console` 首屏禁词测试仍通过，普通用户 PC 首屏未改变。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- `git diff --check`
  - 通过：无 whitespace error。

## 真实上位机 Smoke

目标上位机：`http://192.168.1.11:8787`。

本轮遵守 no-motion 边界：未调用 `/api/base/manual`，未发布 `/cmd_vel`，未做非零运动，
未触碰 WAVE ROVER UART/串口配置、firmware、launch 硬件默认值或 `docs/vendor/**`。
硬件事实入口已读 `docs/vendor/VENDOR_INDEX.md`；本轮未改变 vendor/hardware facts。

先尝试 `stop -> radar start -> scan-proof refresh -> stop`：

- 证据：
  - `artifacts/pc_proxy/16_retry_pc_proxy_scan_proof_refresh.json`
  - `artifacts/remote_capture/17_retry_upper_scan_proof_latest_after_refresh.json`
- 结果：PC proxy 正常转发且 `hard_dangerous_true_fields=[]`，但四项未满足：
  - `scan_once_observed=false`
  - `scan_hz_observed=false`
  - `raw_packet_once_observed=false`
  - `tf_observed=true`
- 定位：先 start lifecycle 再 refresh 会让 refresh runtime 与已有 lifecycle 竞争 LiDAR
  runtime/`/dev/ttyACM0` 观测窗口，仍可能错过 `/scan` 和 raw packet。

最终采用普通 PC 页面“刷新雷达”路径：`stop -> scan-proof refresh(start_runtime=true) -> stop`。

- PC proxy response：
  - `artifacts/pc_proxy/23_refresh_only_pc_proxy_scan_proof_refresh.json`
  - HTTP 200，`proxy_status=refresh_forwarded`，`remote_http_status=200`
  - `latest_readback_key_values.scan_once_observed=true`
  - `latest_readback_key_values.scan_hz_observed=true`
  - `latest_readback_key_values.raw_packet_once_observed=true`
  - `latest_readback_key_values.tf_observed=true`
  - `hard_dangerous_true_fields=[]`
- Upper latest scan proof：
  - `artifacts/remote_capture/24_refresh_only_upper_scan_proof_latest_after_refresh.json`
  - `latest_proof_status=scan_once_hz_raw_packet_tf_observed`
  - `scan_once_observed=true`
  - `scan_hz_observed=true`
  - `raw_packet_once_observed=true`
  - `tf_observed=true`
- Upper radar status after refresh：
  - `artifacts/remote_capture/25_refresh_only_upper_radar_status_after_refresh.json`
  - `scan_status=fresh_scan_proof_observed`
  - `latest_scan_proof_state=scan_once_hz_raw_packet_tf_observed`
  - 四项观测均为 true。
- Stop/readback：
  - `artifacts/pc_proxy/27_refresh_only_pc_proxy_radar_stop_after.json`
  - `proxy_status=lifecycle_forwarded`，`remote_http_status=200`

## 清理验证

- 本地 workstation server：
  - `artifacts/pc_proxy/33_local_final_cleanup_check.log`
  - `127.0.0.1:18787` 无 listening server。
- 远端 helper/device：
  - `artifacts/remote_capture/32_remote_static_tf_cleanup_retry_recheck.log`
  - helper 进程复查为空。
  - `/dev/ttyACM0` 与 `/dev/ttyS5` 的 `lsof` / `fuser` 无输出。
  - `trashbot-upper-robot-api.service` 为 `active`。

## 剩余风险

- PC 页面普通“刷新雷达”路径已通过真实冷启动 smoke；`radar start -> refresh` 路径在本轮证明仍不稳定，不应作为 PC 普通刷新雷达的推荐验收路径。
- 上位机 `/api/radar/status` 仍保留 `continuous_scan_status=not_proven` /
  `scan_continuity_not_observed`，本轮只证明单次 no-motion scan-proof refresh，不证明连续雷达健康、HIL movement、Nav2 execution、真实路线或 delivery success。
- 不需要 Product、Hardware、Autonomy 或 Full-Stack 额外协同；后续若要支持 start 后 read-only refresh，应由 Robot/Hardware 再单独修上位机 lifecycle/read-only refresh 互斥策略。

## 自检

- 未改普通用户 PC 首屏样式、结构或可见内容。
- 未改 `onboard/**`。
- 未改 `docs/vendor/**`。
- 未调用 `/api/base/manual`，未发布 `/cmd_vel`，未触碰底盘运动、WAVE ROVER UART/串口配置或 firmware。
- 已修复验证中发现的 PC 摘要竞态，并补了回归测试。

记录时间：2026-06-11 10:01:33 CST。

## 验收补丁：PC Compact 摘要收口

时间：2026-06-11 10:05 CST。

验收发现：

- `artifacts/pc_proxy/23_refresh_only_pc_proxy_scan_proof_refresh.json` 中
  `latest_readback_key_values.latest_proof_status=raw_packets_parsed`，且
  `blocked_reasons` 混入 direct collector 的旧 scan missing 文案。
- 同轮最终上位机状态
  `artifacts/remote_capture/25_refresh_only_upper_radar_status_after_refresh.json`
  已显示 `latest_scan_proof_state=scan_once_hz_raw_packet_tf_observed`、
  `latest_scan_proof_blocked_reasons=[]`。

修复：

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - radar refresh compact 摘要不再把最终 readback 和原始 payload 混合后递归搜索。
  - `latest_readback_key_values.latest_proof_status` 优先使用
    `radar_status.latest_scan_proof_state`。
  - `latest_scan_proof_blocked_reasons=[]` 时不写入 compact `blocked_reasons`，避免旧
    direct collector blocker 污染 PC 摘要。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 direct collector 为 `raw_packets_parsed` 且带旧 blocker，但最终
    `radar_status.latest_scan_proof_state=scan_once_hz_raw_packet_tf_observed` 的场景。

验证：

- `cd pc-tools/workstation && npm run build && npm run test -- --run && npm run lint`
  - 通过：build 成功，`Test Files 2 passed (2)`，`Tests 89 passed (89)`，lint 无报错。
- `git diff --check`
  - 通过。

未重跑真实上位机原因：

- 本次只修 PC proxy 对同一 refresh response 的 compact 字段选择，不改变上位机请求 body、
  endpoint、timeout、硬件 runtime 或真实采集逻辑。
- 上一轮真实 artifact 已证明 upper 最终 readback 正确；本轮用单元测试复现并固定 PC 摘要
  选择逻辑即可覆盖验收缺口。
