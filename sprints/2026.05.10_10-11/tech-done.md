# Sprint 2026.05.10 10-11 Tech Done

## 实际改动

- Autonomy Algorithm Engineer 在 `test_route_data_recorder_manifest.py` 增加 runtime-style callback 测试。
- 测试用 fake image / odometry 回调驱动真实 `_on_image()` / `_on_odom()`，验证 `route.csv`、keyframe jpg、companion JSON 和 `trashbot.vision_samples.v1` manifest 都会落盘。
- Production `route_data_recorder.py` 未改动；现有 callback 链路可通过测试注入验证。
- Robot Platform Engineer 只读复查下一轮候选：Objective 2/3 应补 `TrashCollection` action 消费 fixed-route status JSON 的集成证明，暂不删除 legacy sleep demo server。
- `OKR.md` 更新当前快照和第 20 轮进度，Objective 4 从约 61% 推进到约 63%。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_nav:src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py` 通过，5 tests OK。
- `python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 27、bringup 9、behavior 105、vision 8。
- `git diff --check` 通过。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，`docker` 命令不可用，无法完成 Docker/Humble colcon build。

## 偏差与风险

- 本轮验证是无 ROS runtime 的 callback 文件写入证明，不替代真实 ROS2 camera / odom bag 或上车采集。
- Docker/Humble build、真实路线数据集、真实 Nav2 route run、WAVE ROVER HIL 仍未完成。
- 下一轮高价值功能推进：补 `TrashCollection` fixed-route status 集成证明，关闭 Objective 2/3 的行为层证据缺口。
