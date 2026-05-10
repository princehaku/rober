# Sprint 2026.05.10 10-11 Tech Plan

## 文件范围

- `src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py`
- `OKR.md`
- `sprints/2026.05.10_10-11/pre_start.md`
- `sprints/2026.05.10_10-11/tech-plan.md`
- `sprints/2026.05.10_10-11/tech-done.md`
- `sprints/2026.05.10_10-11/final.md`

## 技术方案

1. 使用 fake `CvBridge`、fake image message、fake odometry message 和 fake `cv2.imwrite`，绕开 ROS runtime 但调用真实 recorder callback。
2. 通过 `RouteDataRecorder.__new__()` 注入最小实例状态，避免初始化 ROS node。
3. 断言 callback 产物覆盖路线 CSV、keyframe 文件、companion sample JSON、manifest entry、pose、sample ref、context 和 recorder 内部 index/last pose 状态。
4. 保持 production `route_data_recorder.py` 不变；如果现有 callback 不满足契约，再由 Autonomy Engineer 做最小修复。

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_nav:src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py`
- `python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`

## 风险边界

- 不声称完成真实相机、真实 odom、Nav2 或上车采集。
- 不新增视觉模型，不改变 detector 默认行为。
- 不修改 ROS2 interface 字段。
