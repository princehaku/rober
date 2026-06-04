# Tech Done: O9 Fresh Scan Proof Runtime

## sprint_type

sprint_type: epic

## 实际改动

- `sprints/2026.06.05_00-01_o9-fresh-scan-proof-runtime/pre_start.md`
  - 启动 O9/O3/O7 fresh scan proof runtime Epic。
  - 记录最近 2 轮 blocker scan：不重复消费 HTTP 405；本轮聚焦 `ros2_command_unavailable`、`upper_api_scan_not_proven`、missing `/scan`、missing `/lidar/raw_packet` 和 missing TF。
- `sprints/2026.06.05_00-01_o9-fresh-scan-proof-runtime/prd.md`
  - 写清用户价值、验收口径、evidence type 和非目标。
  - 明确本轮不做底盘运动、不发 `/cmd_vel`、不做 HIL、不扩大 PC UI。
- `sprints/2026.06.05_00-01_o9-fresh-scan-proof-runtime/tech-plan.md`
  - 写入 `OKR 最低优先级核对`：当前最低 Objective 是 O9，且本 sprint 针对 O9/O3/O7。
  - 写入 LiDAR vendor 来源：`docs/vendor/VENDOR_INDEX.md` -> `docs/vendor/lidar_pkg_ros2-main/`。
  - 定义 Robot Software Engineer 单 owner 实施计划、允许文件范围、本地/远端验收命令和安全边界。
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
  - 修复 `run_bash()` 的 `TimeoutExpired` 分支：保留进程已输出的 stdout/stderr 片段。
  - 原因：`ros2 topic hz` 和 `tf2_echo` 常靠 timeout 结束；丢弃 timeout 前输出会把已观察到的 hz/TF 误判成未观察。
- `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
  - 增加 `test_run_bash_timeout_preserves_process_output`，覆盖 bytes/string 两类 timeout 输出保留。

## Runtime 证据

Robot Software Engineer 通过 `ssh root@192.168.1.11 -p 37878` 做了 live upper 复核，关键结果：

- `trashbot-upper-robot-api.service` 为 `active`，`/health` 为 ready。
- `/api/radar/status` 显示 `/dev/ttyACM0` 存在，`/dev/lidar` 缺失，`safe_to_control=false`。
- 常规 `POST /api/radar/scan-proof/refresh` 返回 HTTP 200，但 proof 仍为 `blocked_or_not_observed`，`evidence_type=blocked_with_root_cause`。
- 远端默认 zsh / `set -u` 会让 ROS2 setup 出错；用 `bash -lc` 并在 source 阶段放宽 nounset 后，ROS2 graph 只有 `/parameter_events` 和 `/rosout`，常态下无 `/scan`、无 `/lidar/raw_packet`、无 `base_link -> laser_frame` TF。
- 执行 LiDAR-only smoke：`o1_lidar_ros2_scan_smoke.sh --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame` 后，summary 观察到 `/scan` once、`/scan` hz、`/lidar/raw_packet` 和 TF，且 `safe_to_control=false`、未调用 base/manual、未发布 `/cmd_vel`。
- 在 driver/TF 已启动时做受控 refresh，API collector 观察到 `scan_once=true`、`raw_packet=true`，但 hz/TF 受 timeout 输出丢失影响被误判为 false；本轮代码修复正是为消除这个误判。

## OKR 影响

| Objective | 本轮变化 | 判定 |
| --- | --- | --- |
| O9：短周期真实材料破局战役 | 不涨分 | blocker 已从泛泛 `upper_api_scan_not_proven` 收窄为“常态未运行 LiDAR driver/static TF + collector timeout 输出误判”。仍未形成持久 fresh scan proof。 |
| O3：建图、定位、Nav2 与固定路线 | 不涨分 | LiDAR-only smoke 支撑 runtime 方向，但还没有常态 `/scan` proof、SLAM `/map`、AMCL 或 Nav2 消费证据。 |
| O7：PC 运营调试平台 | 不涨分 | 8787 refresh 可返回 blocked artifact，但没有 PC/operator fresh runtime workflow 完成。 |
| O8：Epic 交付节奏与证据治理 | 可记过程进展，不建议涨分 | 本轮完成 Epic plan 和 root-cause 收窄，但两次子 agent 超时暴露 owner 执行节奏仍需收紧。 |

## 验证结果

已运行：

```bash
python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector
```

结果：

```text
Ran 6 tests in 0.642s
OK
```

已运行：

```bash
python3 -m compileall -q onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_lidar_scan_proof_collector.py
```

结果：退出码 0，无输出。

已运行：

```bash
git diff --check -- onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_lidar_scan_proof_collector.py sprints/2026.06.05_00-01_o9-fresh-scan-proof-runtime/tech-done.md
```

结果：退出码 0，无输出。

## 失败定位

- 已解除/收窄：`ros2_command_unavailable` 不再是核心 blocker；ROS2 CLI 在正确 bash/source 环境下可用。
- 当前主 blocker：LiDAR driver/static TF 没有作为常态 runtime 运行，因此普通 refresh 仍读不到 `/scan`、`/lidar/raw_packet` 和 TF。
- 当前软件 bug：timeout 分支丢弃 `ros2 topic hz` / `tf2_echo` 已输出文本，会造成 false negative；本轮已加最小修复和回归。

## 剩余风险

- 未部署持久 LiDAR driver/static TF service 或 launch 管理策略。
- 未证明 fresh `/scan` proof 在普通 8787 refresh 下全量通过。
- 未证明 SLAM `/map`、AMCL、Nav2 lifecycle、固定路线、PC WASD、底盘 HIL、robot ACK 或 `safe_to_control=true`。
- 本轮没有触碰底盘控制，未发 `/cmd_vel`，未调用 `/api/base/manual`，未写 WAVE ROVER `/dev/ttyS5`。
