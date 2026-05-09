# Sprint 2026.05.10 06-07 Tech Done

## 实际改动

- `fixed_route_autonomy.py` 新增 route-wide `keyframe_preflight` 诊断摘要，包含是否启用视觉门控、总 checkpoint、已加载关键帧、缺失关键帧、无效关键帧和路线级视觉准备度。
- 视觉门控开启且整条路线 keyframe 覆盖不完整时，dry-run/导航不会先推进 checkpoint，而是停在 `waiting_visual_gate` 并写出 `keyframe_preflight_failed`。
- `test_fixed_route_dry_run_offline.py` 增加多 checkpoint 缺后续 keyframe 的回归用例，防止路线只验证当前 checkpoint 就提前推进。
- `test_fixed_route_status_static.py` 固化新增 debug status 合同。
- `docs/navigation/fixed_route_workflow.md` 和 `OKR.md` 更新本轮能力、验证口径和剩余风险。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py` 通过，9 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test*.py'` 通过，22 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 22、bringup 9、behavior 101、vision 8。
- `git diff --check` 通过。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，`docker` 命令不可用，无法完成 Docker/Humble colcon build。

## 偏差与风险

- 本轮没有接入真实相机或 Nav2，只增强 fixed-route 离线/状态诊断能力。
- Docker/Humble build、真实 `/odom` + `/camera/image_raw` route 采集、keyframe/live frame 实样匹配、WAVE ROVER HIL 仍是剩余风险。
- Vision/User Touchpoint team 复查发现 Objective 4 下一步高价值任务：让 `route_data_recorder` 产出 `trashbot.vision_samples.v1` manifest 并接入 operator diagnostics，本轮未实现。
