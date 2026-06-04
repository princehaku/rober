# Final: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 最终结论

本轮完成了上一轮要求的 Epic 启动和 L2 并行执行，不再停留在 OKR 纠偏。交付重点是把 O2/O3/O7/O1 的现场能力前置为可执行 software guard：

- 8787 upper API 已有雷达 start/stop、map lifecycle、localize reset、map/localize proof、Nav2 lifecycle 和 elevator status 的 fail-closed 合同。
- PC workstation 已能通过同源 direct-upper 代理展示/触发 radar、map、localize、manual/stop 和 operator report，并支持 operator confirmation、fixture mode 与共享 `evidence_ref`。
- Vision 已有 OpenCV 电梯 taxonomy、ROI/rule baseline、offline eval artifact。
- Nav 已有 ROS-free map quality offline 指标，用于真实 Nav2/地图实跑前筛掉明显不可用地图。
- Hardware 已有 vendor-sourced PC manual HIL 准入边界、同一 `evidence_ref` 绑定与 LiDAR/base UART 隔离准入。

Algorithm follow-up 已复验 O2/O3 software guard：OpenCV fixture eval 可复跑，Nav2 map quality fixture 以预期 exit 1 fail-closed，并已补导航文档和 fixture summary 说明，避免后续把低质量地图 gate fail 当成命令失败。

Robot Software follow-up 已复验 O3/O2 upper API readback guard：Upper API 单测扩展到 23 tests，覆盖 map/localize/Nav2/elevator proof artifact missing/bad JSON 的 fail-closed 行为；`map_list()` 只读 artifact 列举已固定 `sends_commands=false`；接口文档已同步 readback `404/422/500` 和 `not_proven` 边界。

Hardware follow-up 已复验 O1 guard：safe pulse 执行模式要求 operator report 显式携带同一 `evidence_ref`，缺失或不一致都在 manual POST 前 fail-closed；LiDAR raw collector 默认 `/dev/lidar`，并在 open 前拒绝底盘 UART 及其规范化别名。

OKR 完成度不涨。本轮没有真实 runtime、HIL、真实图片、电梯现场、真实 PC 控车或 SLAM/AMCL/Nav2 材料；这些才是下一次涨分依据。

## 实际改动

详见 `tech-done.md`。核心文件：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/elevator_opencv_baseline.py`
- `onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/map_quality_metrics.py`
- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
- `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`
- `onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py`
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
- `docs/interfaces/o7_upper_robot_api.md`
- `docs/product/pc_tools_workstation.md`
- `docs/vision/elevator_opencv_baseline.md`
- `docs/navigation/nav2_map_quality_metrics.md`
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`

## 验证结果

本轮验证通过：

- PC：`npm test -- --run`、`npm run build`、`npm run lint`。
- Upper API：`python3 -m unittest onboard.scripts.test_upper_robot_api`，通过，`Ran 23 tests in 1.759s`，`OK`。
- Vision/Nav：vision 18 tests、nav 54 tests。
- Algorithm fixture：电梯 eval exit 0 且 `field_eval_ready=false`；Nav2 map quality 预期 exit 1 且 `software_guard_pass=false`、`reachable_ratio=0.25`。
- Hardware guard：safe pulse 18 tests、LiDAR scan collector 5 tests、raw packet collector 7 tests。
- Compile：Robot Software 范围 `python3 -m compileall -q onboard/scripts onboard/src` 通过，命令无输出；Algorithm/PC evidence 范围按各 owner 记录通过。
- Docker/Humble：未运行 `bash onboard/scripts/docker_humble_build.sh`；当前 WSL distro 缺 Docker CLI / Docker Desktop WSL integration，`docker info` 输出 `The command 'docker' could not be found in this WSL 2 distro.`，因此未进入 colcon。
- Diff check：Robot Software 收口指定范围 `git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py onboard/src/ros2_trashbot_nav onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup docs/interfaces/o7_upper_robot_api.md docs/product/elevator_assisted_delivery.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic` 通过，命令无输出。
- Hardware scoped diff check：`git diff --check -- onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/o1_lidar_raw_packet_proof_collector.py onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic` 通过，命令无输出。

## OKR 收口

| Objective | 当前比例 | 本轮变化 | 下一步 |
| --- | --- | --- | --- |
| O2 | 约 72% | OpenCV baseline/offline fixture eval software guard 完成，不涨分 | 接真实电梯图片 manifest，输出 eval artifact，再接 ROS2 电梯状态链。 |
| O3 | 约 73% | map/localize/Nav2 upper API 合同和 map quality offline guard 完成，不涨分 | 在上位机配置真实 command hook，采集 `/map`、map file、AMCL/TF 和 Nav2 lifecycle。 |
| O7 | 约 88% | PC operator workflow 消费新合同，含 confirmation/fixture/evidence_ref，不涨分 | 真实浏览器 + 8787 runtime 复跑，采集 radar/map/localize/operator report evidence ref。 |
| O1 | 约 95% | HIL/串口隔离准入、safe pulse evidence_ref 绑定和 LiDAR UART fail-closed 护栏完成，不涨分 | 现场 stop-first 低速 pulse、post-status、`T=1001` 同场和 operator report。 |
| O5/O6 | 约 96% | 未作为本轮主线 | 等 O2/O3/O7 产出真实材料后再消费。 |

## 风险和技术遗留

- 8787 新端点默认 dry-run/stub，真实运行依赖上位机 command hook 和 ROS2 runtime。
- PC UI/API 通过 mock/fetch 和软件合同验证，未证明真实远端 8787 已部署新端点。
- Upper API readback 只证明 missing/bad JSON/fixture artifact 的 fail-closed 合同，不证明真实 SLAM `/map`、AMCL、TF freshness、Nav2 消费 `/scan`+map 或电梯 OpenCV 状态链已在 ROS2 runtime 中运行。
- OpenCV baseline 没有真实电梯图片样本，不能证明真实楼层、门状态或 safe exit。
- HIL 文档不等于 HIL pass，`safe_to_control` 继续为 false。
- Full smoke behavior 包出现过 ResourceWarning 文本但最终 OK；后续若重复出现可单独做 socket lifecycle 清理。

## 下一步建议

下一轮继续当前 Epic，不切回 O5/O6：

1. Robot Software：用上位机 `ssh root@192.168.1.11 -p 37878` 部署/复跑 8787 新端点，至少拿到 radar start/stop 或 map list 的真实 HTTP 材料。
2. Robot Algorithm：采集或接入真实电梯图片 manifest，跑 offline eval，输出 confusion 和 operator summary。
3. Full-stack：用真实 8787 base URL 做 PC rendered smoke，保留 evidence_ref。
4. Hardware：按 HIL boundary 文档做 stop-first 低速 pulse 采证，未满足安全前提则继续保持 `safe_to_control=false`。
