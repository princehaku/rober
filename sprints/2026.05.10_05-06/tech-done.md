# Sprint 2026.05.10 05-06 Tech Done

## 实际改动

- `learn.launch.py` 新增可选 `route_recorder` 开关，默认 `false`，避免基础学习/建图流程强依赖相机和 route 数据集。
- `learn.launch.py` 新增 `route_output_dir`、`route_camera_topic`、`route_odom_topic`、`route_min_distance_m`、`route_frame_id` 参数，并在启用时启动 `route_data_recorder`。
- `test_launch_contract_static.py` 增加学习 launch 的 route recorder 契约测试，覆盖参数声明、条件启动和参数透传。
- `docs/navigation/fixed_route_workflow.md` 增加一键学习采集命令，并保留手动 recorder 调试命令。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过，9 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_bringup/launch/learn.launch.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 20、bringup 9、behavior 101、vision 8。
- `git diff --check` 通过。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，docker 命令不可用，无法完成 Docker/Humble colcon build。

## 偏差与风险

- 本轮只完成 launch wiring、文档和静态契约验证。
- 仍需 ROS2/Humble runtime 验证 `route_recorder:=true` 能在真实 `/odom` 与 `/camera/image_raw` 下产出可用 `route.csv` 和 `keyframes/*.jpg`。
- 仍需真实 keyframe/live frame 匹配、Nav2 waypoint/fixed-route 实跑、Docker/Humble build 和硬件在环验证。
