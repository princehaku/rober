# Sprint 2026.05.10 05-06 Tech Plan

## Owner

Autonomy Algorithm Engineer 主责；Robot Platform Engineer 负责 launch 契约和 smoke 集成验证。

## 文件范围

- `src/ros2_trashbot_bringup/launch/learn.launch.py`
- `src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- `docs/navigation/fixed_route_workflow.md`
- `OKR.md`
- 当前 sprint 文档

## 接口影响

`learn.launch.py` 向后兼容新增 launch arguments：

- `route_recorder`
- `route_output_dir`
- `route_camera_topic`
- `route_odom_topic`
- `route_min_distance_m`
- `route_frame_id`

默认 `route_recorder:=false`，所以基础建图学习入口不新增运行依赖。启用时启动 `ros2_trashbot_nav/route_data_recorder` 并写出固定路线 CSV/keyframes。

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_bringup/launch/learn.launch.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`
- `bash scripts/docker_humble_build.sh`（如当前 WSL 可用 docker）

## 风险边界

本轮不修改 `route_data_recorder.py` 的 runtime 采集逻辑，不声明真实相机、真实里程计、真实路线数据集或 WAVE ROVER HIL 已验证。
