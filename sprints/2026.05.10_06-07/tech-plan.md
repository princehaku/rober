# Sprint 2026.05.10 06-07 Tech Plan

## Owner

Autonomy Algorithm Engineer 主责；Robot Platform Engineer 负责集成验证。

## 文件范围

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `docs/navigation/fixed_route_workflow.md`
- `OKR.md`
- 当前 sprint 文档

## 接口影响

`fixed_route_autonomy` 的 `debug_status_file` 新增 `keyframe_preflight` 字段，面向诊断/调试消费。现有字段保持兼容。

建议字段：

- `enabled`
- `total_checkpoints`
- `loaded_keyframes`
- `missing_keyframes`
- `invalid_keyframes`
- `route_visual_ready`

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`
- `bash scripts/docker_humble_build.sh`（如当前 WSL 可用 docker）

## 风险边界

本轮只做离线/状态诊断能力，不声明真实 keyframe/live frame 匹配样例、Nav2 实跑、摄像头实采或硬件在环已经完成。
