# Side2Side Check: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 对照结论

本轮对照上一轮 `OKR.md` 要求的下一轮 Epic，没有继续堆 Micro sprint，也没有只停在计划。四个 L2 owner 已按文件边界并行交付 software guard：

| 要求 | 本轮结果 | 验收状态 |
| --- | --- | --- |
| PC operator workflow | PC workstation 增加 direct-upper radar/map/localize/operator report UI/API；manual/stop 仍走同源代理，并增加 confirmation、fixture mode 与共享 `evidence_ref` | software_guard 通过 |
| 雷达一键 start/stop | 8787 新增 `/api/radar/start|stop`，PC 新增对应按钮/代理 | software_guard 通过，runtime 未证明 |
| 建图/定位控制 | 8787 新增 `/api/map/start|reset|save|load|list`、`/api/map/proof/latest`、`/api/localize/reset`、`/api/localize/proof/latest`，PC 可消费 | software_guard 通过，SLAM/AMCL runtime 未证明 |
| Nav2/map quality | 新增 ROS-free map quality offline metrics 和 fixture，输出 unknown ratio、waypoint reachability、failure samples | offline guard 通过，Nav2 runtime 未证明 |
| OpenCV 电梯识别 | 新增 taxonomy、ROI/rule baseline、offline eval 和测试 | offline fixture eval 通过，真实图片未证明 |
| HIL/硬件边界 | 新增 vendor-sourced PC manual、同一 evidence_ref 绑定与 LiDAR 串口隔离准入；本次补 operator report ref 缺失/不一致 fail-closed 和 raw collector 规范化底盘 UART 拒绝 | unit/software guard 通过，现场 HIL 未证明 |

Algorithm follow-up 复验补充：

- Vision/Nav discover 稳定：vision 18 tests OK，nav 54 tests OK。
- 电梯 fixture manifest 可复跑：exit 0，software guard pass，field eval 不通过且明确 `needs_real_image_manifest`。
- Nav2 map quality fixture 可复跑：预期 exit 1，JSON 输出正常，fail-closed 原因是 waypoint reachable ratio 只有 0.25。
- 已补 `docs/navigation/nav2_map_quality_metrics.md` 和 fixture summary 的 `expected_exit_code`，避免把预期 fail-closed 误判为脚本异常。

Robot Software follow-up 复验补充：

- Upper API 回归稳定：`python3 -m unittest onboard.scripts.test_upper_robot_api` 通过，`Ran 23 tests in 1.759s`，`OK`。
- `python3 -m compileall -q onboard/scripts onboard/src` 通过，命令无输出。
- 已补 O3/O2 readback fail-closed 回归：map/localize/Nav2/elevator proof artifact 缺失或坏 JSON 时保持 `not_proven`、`readback_sends_commands=false`、`starts_ros2=false`、`safe_to_control=false` 和 `robot_control_executed=false`。
- 已修正 `map_list()` 只读文件列举的 `sends_commands=false` 语义，避免 PC/operator 把本地 artifact 扫描误判成 ROS2/map 命令执行。
- Docker/Humble 未复跑：当前 WSL distro 缺 Docker CLI / Docker Desktop WSL integration，`docker info` 失败于 `The command 'docker' could not be found in this WSL 2 distro.`，未进入 `bash onboard/scripts/docker_humble_build.sh` 或 colcon。

Hardware/O1 follow-up 复验补充：

- Safe pulse runner：`python3 -m unittest onboard.scripts.test_o1_ttyS5_safe_pulse_acceptance` 通过，`Ran 18 tests in 0.421s`，`OK`。
- LiDAR scan proof collector：`python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector` 通过，`Ran 5 tests in 0.666s`，`OK`。
- LiDAR raw packet collector：`python3 -m unittest onboard.scripts.test_o1_lidar_raw_packet_proof_collector` 通过，`Ran 7 tests in 0.258s`，`OK`。
- Scoped `git diff --check` 覆盖 safe pulse、raw collector、HIL boundary 文档和本 sprint 目录：通过，exit 0。
- 本次没有执行真实硬件命令；没有打开 `/dev/ttyS5`、`/dev/lidar`、`/dev/ttyACM0`，没有访问 ROS graph。

## 证据边界

- 可以声明：本轮 O2/O3/O7/O1 的软件护栏和执行入口已往前走，相关测试和 smoke 通过。
- 不能声明：真实控车、真实雷达开关、真实建图定位、真实电梯识别、真实跨楼层送达、HIL pass、robot ACK 或 OKR 完成度提升。

## OKR 对照

| Objective | 本轮是否推进 | 是否涨分 | 原因 |
| --- | --- | --- | --- |
| O2 | 是 | 否 | 有 OpenCV baseline/offline fixture eval，但没有真实图片 eval、状态机接入或受控电梯材料。 |
| O3 | 是 | 否 | 有 map/localize/Nav2 upper API 合同和 map quality offline guard，但没有真实 `/map`、map artifact、AMCL pose 或 Nav2 runtime。 |
| O7 | 是 | 否 | PC operator workflow 已能消费新合同并保留 evidence_ref/fixture 边界，但没有真实 8787/HIL/browser field material。 |
| O1 | 是 | 否 | HIL/串口隔离和 evidence_ref 边界更清楚，operator report ref 缺失/不一致可 fail-closed，但没有真实低速 pulse、post-status 或 ROS feedback topics。 |
| O5/O6 | 否 | 否 | 本轮按优先级没有抢占 O2/O3/O7/O1。 |

## 下一轮 Side-by-side 验收建议

1. 在上位机配置真实 `ROBER_RADAR_START_COMMAND` / `ROBER_RADAR_STOP_COMMAND`，采集 `/api/radar/start|stop` + `/scan` once/hz 证据。
2. 配置真实 map lifecycle command hook，采集 `/api/map/start|save|list` 与 map artifact。
3. 用真实电梯图片 manifest 跑 `elevator_opencv_baseline`，生成 offline eval artifact。
4. 按 `docs/hardware/o1_pc_manual_lidar_hil_boundary.md` 做一次 stop-first 低速 HIL drill，只采一条方向也可以，但必须有 operator report。
