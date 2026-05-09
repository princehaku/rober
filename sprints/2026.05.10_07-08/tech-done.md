# Sprint 2026.05.10 07-08 Tech Done

## 实际改动

- `route_data_recorder.py` 在成功写入 keyframe JPG 后，同步生成 `keyframes/<index>.json` companion sample，记录 `route_pose`、`route_id`、`checkpoint_id`、`event_type=route_keyframe` 和空 `detections`。
- 新增 manifest helper，按 `trashbot.vision_samples.v1` 追加 route keyframe 样本，并支持 bounded entries、坏 manifest 重建和临时文件 + `os.replace()` 写入。
- `learn.launch.py` 新增并透传 `route_id`、`route_sample_manifest_name`、`route_sample_manifest_max_entries`。
- `docs/navigation/fixed_route_workflow.md` 记录学习阶段新增 `keyframes/*.json` 和 `manifest.json` 输出。
- 新增 `test_route_data_recorder_manifest.py` 覆盖 payload contract、manifest bounded append、坏 manifest 重建，以及与 `operator_gateway_diagnostics.summarize_vision_manifest()` 的兼容。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py` 通过，4 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过，9 tests OK。
- `python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py src/ros2_trashbot_bringup/launch/learn.launch.py src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 26、bringup 9、behavior 101、vision 8。
- `git diff --check` 通过。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，`docker` 命令不可用，无法完成 Docker/Humble colcon build。

## 偏差与风险

- 当前尚未完成真实 `/odom` + `/camera/image_raw` route capture；本轮验证是纯函数、静态 launch contract 和 smoke 护栏。
- Docker/Humble colcon build 和 WAVE ROVER HIL 仍取决于当前环境是否可用 Docker/硬件。
- Product/Robot Platform team 复查建议下一轮优先处理 Objective 2：`use_saved_map=false` patrol 学习阶段不能继续模拟成功，应改为 proof-gated。
