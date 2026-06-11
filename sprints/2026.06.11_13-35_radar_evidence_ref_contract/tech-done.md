# Radar Evidence Ref Contract

## sprint_type

micro

## 本轮功能点设计

- 生产者：`onboard/scripts/upper_robot_api.py` 继续只读 `runtime/lidar_scan_proof_latest.json`，不启动雷达、不打开底盘串口、不发送底盘运动。
- 消费者：PC workstation 固定代理、`/api/radar/status` summary、`docs/` 和 sprint artifacts 可以直接读取本轮 LiDAR scan proof 的 evidence id，不再只能用 `generated_at + artifact.path` 旁证。
- 字段策略：如果 LiDAR artifact 或其 `proof` 内已有 `evidence_ref`，保持原值；如果没有但有 `generated_at_ms`，派生稳定 `o1-lidar-scan-proof-<generated_at_ms>`；如果只有 ISO `generated_at`，只用安全可读字符派生 `o1-lidar-scan-proof-<safe-generated-at>`；artifact 缺失、坏 JSON、根节点非 object 或读取失败时不伪造成功 `evidence_ref`，保持 `not_loaded` 或 `null` 并 fail-closed。
- 输出位置：`GET /api/radar/scan-proof/latest` 顶层输出 `evidence_ref` 与 `latest_evidence_ref`；`/api/radar/status` 的 `scan_proof_latest` 与 `latest_scan_proof` 输出同一个 ref；`POST /api/radar/scan-proof/refresh` 成功读取本轮 artifact 后，也把同一个 ref 放到顶层，PC `last_result_evidence_ref` 可直接读取。
- 安全边界：这是只读/证据 ID 合同补强，不改 WAVE ROVER 串口、`/api/base/manual`、`/cmd_vel`、Nav2 goal、Radar start/stop 或 factory firmware。即使 `sends_commands=true` 只表示 LiDAR no-motion evidence helper 行为，所有底盘/运动危险字段仍保持 false。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 LiDAR scan proof evidence ref 派生 helper。
  - `GET /api/radar/scan-proof/latest` 顶层新增 `evidence_ref`、`latest_evidence_ref`。
  - `summarize_lidar_scan_proof_latest_artifact()` 和 `build_radar_latest_scan_proof_status()` 透传同一 ref，`/api/radar/status` 顶层也暴露 `evidence_ref/latest_evidence_ref`。
  - `POST /api/radar/scan-proof/refresh` 在 collector 后重新只读 latest artifact，并把最新 ref 放到顶层，便于 PC proxy `last_result_evidence_ref` 直接读取。
- `onboard/tests/test_upper_robot_api.py`
  - 覆盖显式 `evidence_ref` 保持、`generated_at_ms` 派生、ISO `generated_at` 安全派生、坏 JSON 不伪造 ref、refresh 回包携带 latest ref。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 radar refresh proxy 的 `last_result_evidence_ref` 能读取上位机回包中的 radar evidence ref。
- `docs/hardware/board_sensor_stack_smoke.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录 radar evidence ref 合同和上轮 gap 的修复状态。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 通过，`Ran 24 tests in 0.024s`，`OK`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`
  - 通过，无输出。
- `npm run build`（`pc-tools/workstation`）
  - 通过，`tsc` + `vite build` + server `tsc` 完成。
- `npm run test -- --run`（`pc-tools/workstation`）
  - 通过，`Test Files 2 passed (2)`，`Tests 89 passed (89)`。
- `npm run lint`（`pc-tools/workstation`）
  - 通过，`eslint .` 无输出。
- `git diff --check`
  - 通过，无输出。

真实上位机 smoke（`root@192.168.1.11:37878`，run time `2026-06-11 13:40:10 CST`）：

- 部署：`scp onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py` 后重启 `trashbot-upper-robot-api.service`，服务为 `active`，主进程 `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 ...`。
- `GET http://127.0.0.1:8787/api/radar/scan-proof/latest`：
  - artifact `status=loaded`
  - `evidence_ref=latest_evidence_ref=o1-lidar-scan-proof-1781154380155`
  - `scan_once_observed=true`
  - `scan_hz_observed=true`
  - `raw_packet_once_observed=true`
  - `tf_observed=true`
  - `safe_to_control=false`
  - `sends_motion_commands=false`
- no-motion `POST http://127.0.0.1:8787/api/radar/scan-proof/refresh`，body `{ "timeout_s": 20, "runtime_warmup_s": 15, "start_runtime": true }`：
  - `status=refreshed`
  - `proof_state=scan_once_hz_raw_packet_tf_observed`
  - `evidence_ref=latest_evidence_ref=o1-lidar-scan-proof-1781156280313`
  - `latest_readback_http_status=200`
  - `scan_once_observed=true`
  - `scan_hz_observed=true`
  - `raw_packet_once_observed=true`
  - `tf_observed=true`
  - `all_required_observations_observed=true`
  - `safe_to_control=false`
  - `sends_motion_commands=false`
  - `sends_base_motion_commands=false`
  - `uses_base_uart=false`
  - `robot_control_executed=false`
- refresh 后再次 `GET /api/radar/scan-proof/latest`：
  - `evidence_ref=latest_evidence_ref=o1-lidar-scan-proof-1781156280313`
  - 四项观测仍为 true，运动字段仍 false。
- cleanup：
  - `trashbot-upper-robot-api.service` 为 `active`。
  - `ps` 未发现 `o1_lidar_ros2_scan_smoke|o1_lidar_lifecycle|lidar_driver|static_transform_publisher|scan_proof_collector` 残留。
  - `lsof /dev/ttyS5 /dev/ttyACM0` 和 `fuser -v /dev/ttyS5 /dev/ttyACM0` 均无输出。

Artifacts：

- `sprints/2026.06.11_13-35_radar_evidence_ref_contract/artifacts/live_smoke/latest_after_deploy.json`
- `sprints/2026.06.11_13-35_radar_evidence_ref_contract/artifacts/live_smoke/refresh_after_deploy.json`
- `sprints/2026.06.11_13-35_radar_evidence_ref_contract/artifacts/live_smoke/latest_after_refresh.json`
- `sprints/2026.06.11_13-35_radar_evidence_ref_contract/artifacts/live_smoke/live_smoke_summary.json`
- `sprints/2026.06.11_13-35_radar_evidence_ref_contract/artifacts/live_smoke/cleanup_after_refresh.log`

## 剩余风险

- 本轮只补 radar proof ID/readback 合同，不提升 `safe_to_control`、`delivery_success` 或真实 HIL 完成度。
- refresh 仍会按既有 no-motion helper 启动 LiDAR runtime；它可能短时使用 `/dev/ttyACM0`，但本轮 cleanup 已确认无长期占用。
- 不需要 Product、Hardware、Autonomy 或 Full-Stack 协同；PC 代理已有兼容读取逻辑，本轮只补测试断言。
