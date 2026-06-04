# Tech Done: O9 Scan Hz / TF Runtime Refresh

## sprint_type

sprint_type: micro

## 实际改动

- `onboard/scripts/o1_lidar_scan_proof_collector.py`
  - 将 `/scan` once、`/scan` hz、`/lidar/raw_packet` once 和 `tf2_echo base_link laser_frame` 四个只读 probe 改为并发执行。
  - 原因：API-managed LiDAR-only runtime 是短生命周期窗口，串行采样会让前两个 echo 消耗窗口，导致 `scan_hz` 或 TF 被误判为未观测。
  - 当四项 direct topic/TF proof 全部观测到时，清除旧的 `upper_api_scan_not_proven` 摘要 blocker；partial proof 仍保留该 blocker。
- `onboard/scripts/upper_robot_api.py`
  - 在 `POST /api/radar/scan-proof/refresh` 中增加同轮 runtime summary fallback。
  - 如果 collector 子进程错过短窗口，但 `o1_lidar_ros2_scan_smoke.sh` 的 `summary.json` 已证明四项全量 observed，8787 会把该 summary 原子写回 latest artifact。
  - fallback 明确写入 `runtime_summary_fallback_used=true` 和 `source=api_managed_lidar_runtime_summary`，不把它伪装成 collector 直接观测。
- `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
  - 增加并发调度回归、full direct proof 清理 stale status blocker 回归。
- `onboard/scripts/test_upper_robot_api.py`
  - 增加 runtime summary fallback 更新 latest artifact 的回归。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 同步记录并发采样、runtime summary fallback、安全边界和不可外推项。
- `docs/interfaces/o7_upper_robot_api.md`
  - 同步 8787 refresh/latest 合同，说明 fallback 来源字段和 PC 判读边界。

## 验证结果

本地已运行：

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector
```

结果：

```text
Ran 40 tests in 2.667s
OK (skipped=2)
```

本地已运行：

```bash
python3 -m compileall -q onboard/scripts onboard/src
```

结果：退出码 0，无输出。

本地已运行：

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_upper_robot_api.py onboard/scripts/test_o1_lidar_scan_proof_collector.py docs/interfaces/lidar_ros2_closed_loop.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.05_01-02_o9_scan_hz_tf_runtime/tech-done.md
```

结果：退出码 0，无输出。

远端已同步：

```bash
scp -P 37878 onboard/scripts/upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py root@192.168.1.11:/root/rober/onboard/scripts/
ssh root@192.168.1.11 -p 37878 'systemctl daemon-reload; systemctl restart trashbot-upper-robot-api.service'
```

远端只读状态检查：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; systemctl is-active trashbot-upper-robot-api.service || true; curl -fsS http://127.0.0.1:8787/health; curl -fsS http://127.0.0.1:8787/api/radar/status; curl -fsS http://127.0.0.1:8787/api/radar/scan-proof/latest || true'
```

结果摘要：

```text
service active
health status=ready
2026-06-05 02:47 CST worker 收口复验：
pre-refresh latest 已从 partial 推进为 scan_once_hz_raw_packet_tf_observed
radar/status 仍为 scan_status=not_proven，blocked_reasons=["ros2_lidar_scan_not_connected","scan_continuity_not_observed"]
scan_proof_latest: scan_once=true, scan_hz=true, scan_hz_average_rate_hz=245.403, raw_packet=true, tf=true
safe_to_control=false, sends_motion_commands=false, robot_control_executed=false
```

远端 refresh/latest：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; curl -fsS -X POST http://127.0.0.1:8787/api/radar/scan-proof/refresh; echo; curl -fsS http://127.0.0.1:8787/api/radar/scan-proof/latest'
```

结果摘要：

```text
2026-06-05 02:48 CST worker 收口复验：
refresh status=refreshed
proof_state=scan_once_hz_raw_packet_tf_observed
evidence_type=robot_runtime_material
ros2_runtime_proven=true
scan_runtime_proven=true
blockers_summary=[]
scan_once_observed=true
scan_hz_observed=true
scan_hz_average_rate_hz=257.987
raw_packet_once_observed=true
tf_observed=true
runtime_summary_fallback_used=true
summary_path=/tmp/o1_lidar_ros2_scan_smoke/summary.json
safe_to_control=false
sends_motion_commands=false
sends_base_motion_commands=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

## 失败定位

- 已推进：上一轮 `scan_hz=false` / `tf=false` 中的 TF 已可观测；最终 refresh/latest 通过 runtime summary fallback 拿到四项全量 proof。
- 已收窄 root cause：collector 直接并发 probe 仍可能被 API-managed smoke 的短生命周期和 DDS discovery 竞争影响，表现为 collector 子进程 timeout 无 `/scan` stdout；但同轮 smoke 自身输出文件已经证明 `/scan` once、hz、raw packet 和 TF 全部存在。
- 收口复验新增边界：`/api/radar/scan-proof/latest` 已是 full proof，但 `/api/radar/status` 仍保留 `scan_status=not_proven` 和连续性 blocker；这说明本轮证明的是 fresh proof artifact，不是常态 continuous radar ready。
- 当前机制：8787 latest 采用同轮 smoke summary fallback，不是 collector 子进程直接 stdout proof；artifact 已显式标注来源，避免证据混淆。

## 剩余风险

- 未做 HIL、未做底盘运动、未调用 `/api/base/manual`，也未发布 `/cmd_vel`。
- 未证明 SLAM `/map`、AMCL、Nav2 lifecycle、固定路线、PC WASD、WAVE ROVER ACK、`/odom`、`/imu/data`、`/battery` 或 `safe_to_control=true`。
- LiDAR driver 退出阶段仍可见 ROS context shutdown error；该错误发生在 smoke summary 已采集之后，但后续长稳 runtime 需要单独修复或复验。
- `/dev/lidar` udev 仍未就绪，现场仍用 `/dev/ttyACM0`。

## OKR 影响

- O9：建议 Product/OKR Owner 可考虑小幅涨分，因为 live 8787 refresh/latest 已形成 fresh scan proof runtime material，证据边界为 `robot_runtime_material`，且安全字段保持 fail-closed。
- O3：建议 Product/OKR Owner 可考虑小幅涨分；本轮只证明 LiDAR `/scan` once/hz、raw packet、TF，不证明 SLAM/map/AMCL/Nav2。
- O7：建议 Product/OKR Owner 可考虑小幅涨分；8787 API refresh/latest 已可返回可读 runtime proof，但 PC 按钮同源触发未在本轮复验。
- O1/O2/O5/O6/O8：本轮不建议涨产品分。

## 协同建议

- Product/OKR Owner：决定 O9/O3/O7 是否按 `robot_runtime_material` 小幅更新百分比。
- Hardware Infra Engineer：后续若进入长稳或 HIL，继续按 vendor 资料确认 `/dev/lidar` udev 和现场安全边界。
- Robot Algorithm Engineer：后续可基于 fresh `/scan` 进入 SLAM/map/Nav2 消费证据，不应把本轮材料外推成导航已通过。
- Full-stack Software Engineer：后续复验 PC refresh 按钮是否消费 8787 latest 的 `runtime_summary_fallback_used` 和 `scan_hz_average_rate_hz`。
