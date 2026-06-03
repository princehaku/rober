# 2026.06.03 18-19 O7 scan proof PC visibility tech-done

## sprint_type

micro

## Owner 与流程说明

- 目标 Objective：O1 最低优先级材料的 PC 可见性补齐，同时不把 PC 可见性写成真实 `/scan` 或 HIL。
- 主责 owner：`full-stack-software-engineer`。
- Team 执行：本轮先并行派发 `robot-hardware-engineer` 做远端 scan-proof readback 部署/验证、`full-stack-software-engineer` 做 PC 消费；两个 agent 均超时未正常 closeout。工作树只留下 full-stack PC 改动，协调者关闭 agent 后完成验收与最小文案修正，并在本文记录流程偏差。
- 硬件/远端动作边界：协调验收只做 SSH + curl 只读检查；未发送 `/api/base/manual`，未发送 `T=1/T=13/T=130/T=131`，未发送 `/cmd_vel`，未启动 LiDAR driver，未发送 `A5 60`。

## 已读资料与来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `sprints/2026.06.03_17-18_o1-lidar-scan-proof-artifact/tech-done.md`
- `docs/interfaces/o7_upper_robot_api.md`
- `docs/interfaces/o7_direct_upper_pc_api.md`
- `docs/interfaces/o7_realtime_hardware_sources.md`

## 实际改动

- `pc-tools/workstation/src/server/o7LiveOperatorPanel.ts`
  - 从 8787 `/api/status.radar.scan_proof_latest` 消费 LiDAR scan proof artifact 摘要。
  - 在 live operator payload 增加 `lidar_radar.scan_proof_latest`，包含 artifact status、freshness、age、latest proof status、`/scan` once、raw packet once、blocked reasons 和只读安全字段。
  - loaded artifact 但 proof 仍 blocked 时，fallback blocker 使用 `radar_scan_proof_blocked_or_not_observed`，不误报为未加载。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - 在 direct upper status summary 增加 `radar_scan_proof_artifact_status`、`radar_scan_proof_freshness_status`、`radar_scan_proof_age_seconds`、`radar_scan_proof_latest_status` 和 `radar_scan_proof_blockers`。
  - 同步修正 loaded-but-blocked fallback。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 O7 direct upper 和 live operator contract。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 在 LiDAR/地图卡片展示 Scan proof 摘要和 top blockers。
  - 在 PC 本机 8787 卡片展示 scan proof latest status。
  - 明确展示只读边界：PC 不启动 collector、不发送 `A5 60`、不执行底盘控制。
- `docs/interfaces/o7_direct_upper_pc_api.md`
  - 补充 direct upper scan proof summary 字段、前端入口和 2026-06-03 当前远端 readback 口径。
- `docs/interfaces/o7_realtime_hardware_sources.md`
  - 补充 PC 消费 `radar.scan_proof_latest` 的字段和安全边界。
- `OKR.md`
  - 添加 `2026.06.03_18-19_o7-scan-proof-pc-visibility` 补充证据；O1/O7 百分比均不调整。

## 远端只读验收结果

执行：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'set -u; curl -fsS http://127.0.0.1:8787/health; curl -i -sS http://127.0.0.1:8787/api/radar/scan-proof/latest | head -80; curl -fsS http://127.0.0.1:8787/api/radar/status | head -c 4000'
```

关键结果：

- `GET /health` 返回 `status=ready`。
- `GET /api/radar/scan-proof/latest` 返回 HTTP 200。
- readback artifact `status=loaded`，`schema=trashbot.o1.lidar_scan_proof.v1`，`bytes_read=8412`。
- latest proof `status=blocked_or_not_observed`。
- `scan_once_observed=false`。
- `raw_packet_once_observed=false`。
- blocker 仍包括 `ros2_humble_setup_missing`、`rober_install_setup_missing`、`ros2_command_unavailable`、`upper_api_scan_not_proven`。
- `GET /api/radar/status.scan_proof_latest.http_status=200`，artifact `loaded`。
- 安全字段保持 `safe_to_control=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。

## 本地验证结果

```bash
cd pc-tools/workstation && npm run test
```

结果：`Test Files 2 passed (2)`，`Tests 76 passed (76)`。

```bash
cd pc-tools/workstation && npm run build
```

结果：`vite v7.3.3 building client environment for production...`，`✓ built in 2.08s`，server/client TypeScript build 通过。

```bash
cd pc-tools/workstation && npm run lint
```

结果：exit 0，无输出。

后续还需协调者执行 scoped/full diff-check 和最终 git commit。

## OKR 进度影响

- O1：保持约 95.5%。本轮只是让 scan proof artifact/readback/blocker 被 PC operator 看见，不证明真实 `/scan`。
- O5：保持约 96%。
- O6：保持约 96%。
- O7：保持约 98.6%。PC operator toolchain 更完整，但仍不证明生产路径或真实控制。

## 剩余风险

- 真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2 仍未证明。
- 远端 ROS2 Humble setup、当前 `/root/rober/onboard/install/setup.bash` 和 `ros2` 仍缺失。
- 本轮没有部署新的 `onboard/scripts/upper_robot_api.py`，因为远端 readback 已能返回 HTTP 200 和 artifact loaded。
- 本轮没有真实 HIL、ACK、`/odom`、`/imu/data`、`/battery`、manual control、`safe_to_control=true` 或 delivery success。
- 两个初始 worker 和一个小修 worker 均超时，后续类似远端任务应缩短 worker 范围，要求先返回中间日志，再执行长验证。
