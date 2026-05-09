# Sprint 2026.05.10 07-08 Tech Plan

## Owner

Autonomy Algorithm Engineer 主责；User Touchpoint Full-Stack Engineer 校验 diagnostics 兼容；Robot Platform Engineer 做集成验证。

## 文件范围

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`
- `src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py`
- `src/ros2_trashbot_bringup/launch/learn.launch.py`
- `src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- `docs/navigation/fixed_route_workflow.md`
- `OKR.md`
- 当前 sprint 文档

## 接口影响

`route_data_recorder` 新增参数：

- `route_id`
- `sample_manifest_name`
- `sample_manifest_max_entries`

学习阶段输出新增：

- `keyframes/*.json`
- `manifest.json`，schema 为 `trashbot.vision_samples.v1`

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- `python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py src/ros2_trashbot_bringup/launch/learn.launch.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`
- `bash scripts/docker_humble_build.sh`（如当前 WSL 可用 docker）

## 风险边界

本轮只做学习数据产物和诊断 contract，不启动默认 detector，不新增硬件假设，不声明真实摄像头/里程计采集已经完成。
