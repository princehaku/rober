# O1/O7 Realtime Scan Map Split Tech Plan

## 技术方案

新增或扩展 PC live operator contract，把雷达与地图状态拆成两层：

- `realtime_radar`：从 8787 `radar.scan_proof_latest` 摘要派生，只认 `latest_scan_once_observed` 与可用的 hz 观测字段；raw packet proof 不参与 ready 判定。
- `realtime_map`：从 `/scan` readiness 和已有/未来 map artifact 摘要派生。当前没有真实 map/SLAM artifact 时，状态应为 `waiting_for_radar` 或 `waiting_for_mapping`。
- `lidar_radar.raw_packet_proof_latest` 保留为 diagnostics，用于详情/工程折叠区。

Robot side 只做 `/scan` proof/runtime 状态摘要与 smoke/collector 验证，不启动底盘，不碰 `/dev/ttyS5`。

## Task A - Full-Stack

Owner: `full-stack-software-engineer`

文件范围：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7LiveOperatorPanel.ts`
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_live_operator_panel.md`

要求：

- 扩展 `O7LiveOperatorPanelResponse`，新增 `realtime_radar` 与 `realtime_map`。
- 后端从 `scan_proof_latest` 派生 radar 状态；只有 `/scan` 观测字段为真才 ready。
- UI 将现有地图卡片拆为两个区块，raw packet proof 放入诊断详情，不参与状态灯。
- 回归测试覆盖：
  - raw packet observed + `/scan` blocked => radar blocked，map waiting radar。
  - `/scan` observed + map absent => radar ready，map waiting mapping。
  - 首屏不含 `雷达未接入 / 等待建图`。

验收命令：

```bash
cd pc-tools/workstation && npm test -- --run
cd pc-tools/workstation && npm run build
```

## Task B - Robot Software

Owner: `robot-software-engineer`

文件范围：

- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`
- `onboard/scripts/o1_upper_computer_readiness_probe.py`
- `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
- `onboard/scripts/test_o1_upper_computer_readiness_probe.py`
- `docs/interfaces/o7_upper_robot_api.md`

要求：

- 确认 collector/smoke summary 能表达 `/scan` once、`/scan` hz、`/lidar/raw_packet` once、TF 四个独立结果。
- 如现有字段不足，补机器可读字段，但不得启动 driver 或发送 LiDAR start command，除非是在 LiDAR-only smoke 脚本内。
- 不改底盘控制 API，不打开 `/dev/ttyS5`。
- 文档同步说明 `/scan` proof 与 raw packet proof 的边界。

验收命令：

```bash
python3 -m unittest onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
python3 -m compileall -q onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/o1_upper_computer_readiness_probe.py
```

## Task C - Hardware Source Review

Owner: `robot-hardware-engineer`

文件范围：

- 只读：`docs/vendor/VENDOR_INDEX.md`
- 只读：`docs/vendor/lidar_pkg_ros2-main/README.md`
- 只读：`docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- 只读：`docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- 只读：`docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- 可改：如发现文档事实缺口，仅允许修改 `docs/interfaces/o7_upper_robot_api.md` 或在返回中指出需 Robot Software 更新。

要求：

- 复核 `/dev/ttyACM0`、`/dev/lidar`、150000 baud、`A5 60`、停止序列、`/scan`、`/lidar/raw_packet`、frame 的资料来源。
- 不写硬件配置，不运行硬件命令，不打开串口。

验收命令：

```bash
sed -n '1,320p' docs/vendor/VENDOR_INDEX.md >/tmp/o1_vendor_index_readback.txt
```

## Task B2 - 8787 Scan Proof Summary Integration

Owner: `robot-software-engineer`

文件范围：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `docs/interfaces/o7_upper_robot_api.md`

触发原因：

- Task A 的 PC contract 已经只认 `radar.scan_proof_latest.latest_scan_once_observed`
  与 `latest_scan_hz_observed`。
- Task B 的 collector artifact 已经产出 `/scan` once、`/scan` hz、raw packet once、TF
  四项 proof。
- 当前 8787 `GET /api/radar/status` 的 compact summary 仍只暴露 once/raw 两项，
  会导致 PC 即使读取到新 artifact，也无法把真实 `/scan` hz 观测映射到实时雷达 ready。

要求：

- 扩展 `summarize_lidar_scan_proof_latest_artifact()`，在只读 artifact 的前提下暴露：
  - `latest_scan_hz_observed`
  - `latest_scan_hz_average_rate_hz`
  - `latest_tf_observed`
  - `latest_all_required_observations_observed`
  - 如实现上更稳妥，可同时暴露 `latest_required_observations` 的 compact 摘要。
- 保持 readback 边界：不启动 ROS2、不打开 `/dev/ttyACM0`、不打开 `/dev/ttyS5`、不发送任何 LiDAR 或底盘命令。
- 更新 `test_upper_robot_api.py` 覆盖新 artifact 字段，兼容旧 artifact 缺少 hz/tf 字段时返回 `None`。
- 更新 `docs/interfaces/o7_upper_robot_api.md`，说明 `GET /api/radar/status` compact summary 已包含四项 proof 摘要，PC 主状态灯仍只认 `/scan` once/hz。

验收命令：

```bash
python3 -m unittest onboard/scripts/test_upper_robot_api.py onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/o1_upper_computer_readiness_probe.py
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节最低 Objective 是 O1（约 96%，real `/scan` not_proven，与 O5/O6 约 96% 并列但 O1 是当前用户指定问题）。本 sprint 直接针对 O1 的 LiDAR `/scan` 缺口，并把 O7 PC 首屏可见性同步修正，因此符合最低优先级软提醒。

## 集成验收

主节点验收：

```bash
git diff --stat
cd pc-tools/workstation && npm test -- --run && npm run build && npm run lint
python3 -m unittest onboard/scripts/test_upper_robot_api.py onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/o1_upper_computer_readiness_probe.py
```

渲染验收：

- 启动 PC workstation dev/API。
- 浏览器打开首屏。
- 确认两个区块分别为 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)`。
- 确认无组合标题 `雷达未接入 / 等待建图`。
- 记录 console error/warn 和截图。
