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

## 2026-06-05 延续记录：API-managed runtime hook

后续 Robot Software worker 做了本地 API-managed LiDAR-only runtime hook diff，涉及：

- `onboard/scripts/upper_robot_api.py`
  - 新增 `ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND` / warmup 配置入口。
  - `POST /api/radar/scan-proof/refresh` 可在配置后先启动白名单 LiDAR-only smoke runtime，再运行 collector 读取 `/scan`、`/lidar/raw_packet` 和 `base_link -> laser_frame` TF。
  - 继续禁止底盘 UART `/dev/ttyS5`、`/api/base/manual`、`/cmd_vel`、WAVE ROVER `T=1/T=13/T=130/T=131` 和 shell 控制符；响应保持 `safe_to_control=false`、`sends_base_motion_commands=false`。
- `onboard/scripts/test_upper_robot_api.py`
  - 增加 API-managed runtime happy path、unsafe command 拒绝、runtime 失败仍 blocked 三类回归。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 同步说明 API-managed runtime hook 的边界：可启动 LiDAR-only runtime，但不能外推为底盘 ACK、HIL、Nav2/SLAM 消费或 delivery success。

当前验证状态：

- worker 报告本地 `python3 -m unittest onboard.scripts.test_upper_robot_api` 已通过。
- worker 报告本地 `python3 -m compileall -q onboard/scripts onboard/src` 已通过。
- Robot Software 验收 worker 复跑 `python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector`，结果 `Ran 37 tests`，`OK (skipped=2)`。
- Robot Software 验收 worker 复跑 `python3 -m compileall -q onboard/scripts onboard/src`，退出码 0。
- Robot Software 验收 worker 运行 `git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/lidar_ros2_closed_loop.md`，退出码 0。

远端部署状态：

- 已同步 `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
- 已写入 systemd drop-in `/etc/systemd/system/trashbot-upper-robot-api.service.d/20-lidar-scan-proof-runtime.conf`，配置 `ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND="bash /root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame"`，并补 `HOME/USER/LOGNAME/ROS_HOME/ROS_LOG_DIR`。
- 已执行 service reload/restart；最终只读取证 worker 确认 service `active`、`/health` ready。
- 最终 live `POST /api/radar/scan-proof/refresh` 返回 `status=refreshed`、`proof_state=partially_observed`、`evidence_type=blocked_with_root_cause`。
- 最终 live latest 返回 `status=loaded`、`proof.status=partially_observed`；`scan_once=true`、`raw_packet=true`、`scan_hz=false`、`tf=false`、`all_required=false`。
- 安全字段保持：`safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`。

owner timeout / blocker：

- 第一个 Robot Software worker 超时/中断：未完成验证、未部署、未形成可验收材料。
- 第二个 Robot Software worker 产出本地 hook diff 并报告本地测试通过，但未完成最终 diff-check、未完成远端部署取证、未更新本文件。
- 第三个 Robot Software 验收 worker 完成本地 diff-check、远端部署和 service env 修正，但中断前未完成最终 refresh。
- 第四个只读取证 worker 最终确认 API hook 已让 live refresh 从全缺失推进到 partial：`scan_once/raw_packet` 可观察，`scan_hz/TF` 仍缺失。
- Product 判定：这属于 O8 owner-timeout/process evidence 和 O9 blocker 收窄；不能包装成 O9/O3/O7 产品能力。

证据边界：

- `evidence_type=software_guard`：API-managed runtime hook 本地 diff、单元测试和接口文档属于软件护栏。
- `evidence_type=blocked_with_root_cause`：远端 fresh proof 未完成，当前 blocker 是 `scan_hz=false`、`tf=false`，即 scan continuity 和 `base_link -> laser_frame` TF 未观测到。
- 只有 live 8787 latest artifact 明确包含 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、collector log、artifact timestamp、`safe_to_control=false` 和 not_proven 边界时，才可升级为 `robot_runtime_material`。

## OKR 影响

| Objective | 本轮变化 | 判定 |
| --- | --- | --- |
| O9：短周期真实材料破局战役 | 不涨分 | blocker 已从泛泛 `upper_api_scan_not_proven` 收窄为 live refresh partial：`scan_once/raw_packet` 可观察，`scan_hz/TF` 缺失；仍没有完整 fresh `/scan` runtime material，因此不计完成。 |
| O3：建图、定位、Nav2 与固定路线 | 不涨分 | LiDAR-only smoke 与 API-managed hook 支撑 runtime 方向，但还没有完整 live `/scan` proof、SLAM `/map`、AMCL 或 Nav2 消费证据。 |
| O7：PC 运营调试平台 | 不涨分 | 8787 refresh 可返回 blocked artifact，hook 本地可让 API 管理 LiDAR-only runtime；但没有 PC/operator fresh runtime workflow 完成。 |
| O8：Epic 交付节奏与证据治理 | 可记过程进展，不建议涨分 | 本轮完成 Epic plan 和 root-cause 收窄，但两次子 agent 超时暴露 owner 执行节奏仍需收紧。 |

## 验证结果

已运行：

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector
```

结果：

```text
Ran 37 tests in 2.387s
OK (skipped=2)
```

已运行：

```bash
python3 -m compileall -q onboard/scripts onboard/src
```

结果：退出码 0，无输出。

已运行：

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/lidar_ros2_closed_loop.md
```

结果：退出码 0，无输出。

已运行：

```bash
ssh root@192.168.1.11 -p 37878 '... curl -X POST http://127.0.0.1:8787/api/radar/scan-proof/refresh; curl http://127.0.0.1:8787/api/radar/scan-proof/latest'
```

结果摘要：

```text
service active, health ready
refresh status=refreshed, proof_state=partially_observed, evidence_type=blocked_with_root_cause
latest proof.status=partially_observed
scan_once=true, raw_packet=true, scan_hz=false, tf=false, all_required=false
safe_to_control=false, sends_base_motion_commands=false, robot_control_executed=false
```

历史已运行：

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
- 已解除/收窄：API-managed runtime hook 已部署到 upper，普通 refresh 已能观察 `scan_once=true` 和 `raw_packet=true`。
- 当前主 blocker：`scan_hz=false` 和 `tf=false`，即 scan continuity 与 `base_link -> laser_frame` TF 未被最终 refresh 观测到。
- 已修复软件 bug：timeout 分支丢弃 `ros2 topic hz` / `tf2_echo` 已输出文本，会造成 false negative；本轮已加最小修复和回归。

## 剩余风险

- 未证明 LiDAR driver/static TF 能在 8787 refresh 生命周期内稳定产出 `scan_hz=true` 和 `tf=true`。
- 未证明 fresh `/scan` proof 在普通 8787 refresh 下全量通过。
- 未证明 SLAM `/map`、AMCL、Nav2 lifecycle、固定路线、PC WASD、底盘 HIL、robot ACK 或 `safe_to_control=true`。
- 本轮没有触碰底盘控制，未发 `/cmd_vel`，未调用 `/api/base/manual`，未写 WAVE ROVER `/dev/ttyS5`。
