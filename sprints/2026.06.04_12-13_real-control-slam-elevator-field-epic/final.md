# Final: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 最终结论

本轮完成了上一轮要求的 Epic 启动和 L2 并行执行，不再停留在 OKR 纠偏。交付重点是把 O2/O3/O7/O1 的现场能力前置为可执行 software guard：

- 8787 upper API 已有雷达 start/stop、map lifecycle、localize reset 的 fail-closed 合同。
- PC workstation 已能通过同源 direct-upper 代理展示/触发 radar、map、localize、manual/stop 和 operator report。
- Vision 已有 OpenCV 电梯 taxonomy、ROI/rule baseline 和 offline eval artifact。
- Hardware 已有 vendor-sourced PC manual HIL 与 LiDAR 串口隔离准入。

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
- `docs/interfaces/o7_upper_robot_api.md`
- `docs/product/pc_tools_workstation.md`
- `docs/vision/elevator_opencv_baseline.md`
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`

## 验证结果

本轮验证通过：

- PC：`npm test -- --run`、`npm run build`、`npm run lint`。
- Upper API：`python3 -m unittest onboard.scripts.test_upper_robot_api`。
- Vision/Nav：vision 18 tests、nav 52 tests。
- Hardware collector：LiDAR scan/raw packet collector 9 tests。
- Compile：`python3 -m compileall -q onboard/scripts onboard/src pc-tools/evidence`。
- Full smoke：`PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh`，interfaces 6、hardware 68、nav 52、bringup 11、behavior 841、vision 18，全通过。
- Diff check：本轮相关范围 `git diff --check` 全通过。

## OKR 收口

| Objective | 当前比例 | 本轮变化 | 下一步 |
| --- | --- | --- | --- |
| O2 | 约 72% | OpenCV baseline/offline fixture eval software guard 完成，不涨分 | 接真实电梯图片 manifest，输出 eval artifact，再接 ROS2 电梯状态链。 |
| O3 | 约 73% | map/localize upper API fail-closed 合同完成，不涨分 | 在上位机配置真实 command hook，采集 `/map`、map file、AMCL/TF。 |
| O7 | 约 88% | PC operator workflow 消费新合同，不涨分 | 真实浏览器 + 8787 runtime 复跑，采集 radar/map/localize/operator report evidence ref。 |
| O1 | 约 95% | HIL/串口隔离准入完成，不涨分 | 现场 stop-first 低速 pulse、post-status、`T=1001` 同场和 operator report。 |
| O5/O6 | 约 96% | 未作为本轮主线 | 等 O2/O3/O7 产出真实材料后再消费。 |

## 风险和技术遗留

- 8787 新端点默认 dry-run/stub，真实运行依赖上位机 command hook 和 ROS2 runtime。
- PC UI/API 通过 mock/fetch 和软件合同验证，未证明真实远端 8787 已部署新端点。
- OpenCV baseline 没有真实电梯图片样本，不能证明真实楼层、门状态或 safe exit。
- HIL 文档不等于 HIL pass，`safe_to_control` 继续为 false。
- Full smoke behavior 包出现过 ResourceWarning 文本但最终 OK；后续若重复出现可单独做 socket lifecycle 清理。

## 下一步建议

下一轮继续当前 Epic，不切回 O5/O6：

1. Robot Software：用上位机 `ssh root@192.168.1.11 -p 37878` 部署/复跑 8787 新端点，至少拿到 radar start/stop 或 map list 的真实 HTTP 材料。
2. Robot Algorithm：采集或接入真实电梯图片 manifest，跑 offline eval，输出 confusion 和 operator summary。
3. Full-stack：用真实 8787 base URL 做 PC rendered smoke，保留 evidence_ref。
4. Hardware：按 HIL boundary 文档做 stop-first 低速 pulse 采证，未满足安全前提则继续保持 `safe_to_control=false`。
