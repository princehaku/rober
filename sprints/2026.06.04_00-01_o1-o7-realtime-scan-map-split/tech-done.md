# O1/O7 Realtime Scan Map Split Tech Done

## sprint_type

epic

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `O7LiveOperatorPanelResponse`，新增 `realtime_radar` 与 `realtime_map`。
  - `realtime_radar.ready` 只允许由 `/scan` once 与 `/scan` hz 同时观测点亮。
- `pc-tools/workstation/src/server/o7LiveOperatorPanel.ts`
  - 从 8787 `radar.scan_proof_latest` 派生 `实时雷达 (/scan)`。
  - `raw_packet_proof_latest` 只保留为诊断材料，固定不参与 ready 判定。
  - 没有 `/scan` once+hz 时 `realtime_map.status=waiting_for_radar`；有 `/scan` 但无 map/SLAM artifact 时 `waiting_for_mapping`。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 首屏拆成 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)` 两个独立区块。
  - 状态灯“雷达”读取 `realtime_radar.ready`；raw packet 下沉到诊断详情。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 raw packet observed 但 `/scan` blocked 时 radar 仍 blocked。
  - 覆盖 `/scan` once+hz observed 但 map absent 时 radar ready、map waiting mapping。
  - 覆盖首屏不出现组合标题 `雷达未接入 / 等待建图`。
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
  - proof 输出拆成 `scan_once`、`scan_hz`、`raw_packet_once`、`tf` 四项观测。
  - 顶层补 `scan_hz_observed`、`scan_hz_average_rate_hz`、`tf_observed`、`all_required_observations_observed`。
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`
  - LiDAR-only smoke summary 使用同一套四项 required observations。
  - 保持拒绝 `/dev/ttyS5`，不触碰底盘控制。
- `onboard/scripts/o1_upper_computer_readiness_probe.py`
  - readiness probe 命令/摘要包含 `/scan` hz 与 `tf2_echo base_link laser_frame`。
- `onboard/scripts/upper_robot_api.py`
  - 8787 `GET /api/radar/status` 的 `scan_proof_latest` compact summary 补齐 `latest_scan_hz_observed`、`latest_scan_hz_average_rate_hz`、`latest_tf_observed`、`latest_all_required_observations_observed` 与 `latest_required_observations`。
  - 旧 artifact 缺少 hz/TF 字段时保持 `None`，不把缺省解释成 ready。
- 测试与文档同步：
  - `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
  - `onboard/scripts/test_o1_upper_computer_readiness_probe.py`
  - `onboard/scripts/test_upper_robot_api.py`
  - `docs/interfaces/o7_live_operator_panel.md`
  - `docs/interfaces/o7_upper_robot_api.md`

## 硬件资料复核

Hardware Source Review 只读复核了 `docs/vendor/VENDOR_INDEX.md` 及 LiDAR vendor 资料，确认：

- 当前观察到的 LiDAR 候选口是 `/dev/ttyACM0`，production 更推荐 `/dev/lidar` 或 STC by-id udev。
- vendor ROS2/STC baudrate 是 `150000`。
- LiDAR start bytes 是 `A5 60`，stop sequence 是 `A5 00 A5 65 A5 65`。
- vendor driver 发布 `LaserScan` 到相对 topic `scan`，无 namespace 时即 `/scan`。
- vendor driver 不发布 `/lidar/raw_packet`；该 topic 属于项目工程诊断/历史协议，不是 `/scan` ready 证据。

## 验证结果

PC 验收由 Full-Stack 子 agent 执行：

```text
cd pc-tools/workstation && npm test -- --run
Test Files 2 passed (2)
Tests 81 passed (81)
```

```text
cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 2.47s
```

```text
cd pc-tools/workstation && npm run lint
eslint .
exit code 0
```

Robot Software Task B 验收：

```text
python3 -m unittest onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
Ran 14 tests in 1.712s
OK
```

```text
python3 -m compileall -q onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/o1_upper_computer_readiness_probe.py
exit code 0
```

Robot Software Task B2 验收：

```text
python3 -m unittest onboard/scripts/test_upper_robot_api.py onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
Ran 30 tests in 3.106s
OK
```

```text
python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/o1_upper_computer_readiness_probe.py
exit code 0
```

Hardware readback：

```text
sed -n '1,320p' docs/vendor/VENDOR_INDEX.md >/tmp/o1_vendor_index_readback.txt
exit code 0
```

## Rendered Smoke

Full-Stack 子 agent 说明 Browser 插件不可用，按计划使用 repo 内 Playwright：

- Vite `5173-5175` 被占用，实际使用 `http://127.0.0.1:5176/`。
- 截图：`/tmp/o7-live-operator-panel-final-20260604.png`。
- 首屏包含 `实时雷达 (/scan)`：通过。
- 首屏包含 `实时图 (SLAM/map)`：通过。
- 首屏不包含 `雷达未接入 / 等待建图`：通过。
- raw packet proof 只在诊断/guardrail 文案中出现，不点亮 radar ready：通过。
- 首屏 offer 请求数 `0`：通过。
- 点击“重新连接预览”后 offer 请求数 `1`：通过。
- console error/warn：`[]`。
- page errors：`[]`。

## 未完成事项和风险

- 本 sprint 自身没有重复运行真实上位机 LiDAR-only smoke；真实 `summary.json` 由并行
  `sprints/2026.06.04_00-01_o1-upper-ros2-bootstrap-continue/tech-done.md` 记录。
- 结合并行 O1 micro，首个真实 ROS2 `/scan` once、`/scan` hz、
  `/lidar/raw_packet` 和 TF smoke 已 observed；本 sprint 仍不证明 SLAM/map、
  Nav2、长稳、production udev、driver 优雅退出或 HIL。
- `OKR.md` 已由 Product/OKR 收口按真实 smoke 证据保守更新：O1 约 97%，
  O7 约 98.9%；该调整不外推为 HIL、`safe_to_control=true` 或完整上车任务。
- `raw_packet_proof_latest` 继续只能作为诊断材料，不能让 PC 显示“实时雷达已接入”。
