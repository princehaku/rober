# Autonomous Fixed Route Real Nav2 Default Micro Sprint

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`：固定路线 autonomous 默认改为真实 Nav2 执行，`fixed_route_dry_run=false`；视觉 keyframe gate 改为显式 opt-in，`enable_visual_gate=false`，避免相机无帧或默认 dry-run 让自动驾驶“启动但不动”。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：新增静态合同断言，锁定上述两个默认值。
- `docs/navigation/fixed_route_workflow.md`、`docs/acceptance/robot_bringup_checklist.md`、`docs/product/pc_free_roam_mapping_design.md`、`pc-tools/README.md`：同步说明真实执行默认、dry-run/视觉 gate 回退参数和剩余安全边界。

## 验证结果

- 通过：`python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`，结果 `Ran 19 tests` / `OK`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`，结果 `Ran 19 tests` / `OK`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Nav2 restore|current Nav2 blocker|starts map recording before auto sweep|shared camera status pending"`，结果 `4 passed | 201 skipped (205)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`354 passed (354)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，结果 `Summary: 6 packages finished [43.8s]`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 launch 默认和文档，没有在真实小车上发送 Nav2、manual、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实自动驾驶仍依赖现场安全确认、停止兜底、Nav2 服务、地图、定位、TF 和底盘控制链路；这些需要上车 HIL 复验。
