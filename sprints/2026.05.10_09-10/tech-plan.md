# Sprint 2026.05.10 09-10 Tech Plan

## 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `docs/vision/perception_upgrade_evaluation.md`
- `OKR.md`
- `sprints/2026.05.10_09-10/tech-done.md`
- `sprints/2026.05.10_09-10/final.md`

## 技术方案

1. 在 `summarize_vision_manifest()` 中统计 `event_type` 分布。
2. 为 manifest samples 生成 bounded `review_queue`，优先选取 anomaly、route_keyframe、低置信度检测和未标注样本。
3. 每条 review item 保留 `sample_id`、`sample_ref`、`timestamp`、`context`、`detection_count`、`max_confidence`、`reason`。
4. 手机 diagnostics panel 展示 review queue 数量和最新待复核样本。
5. 更新 Objective 4 文档和 OKR 快照，明确这只是软件诊断闭环，不等于真实相机数据集已完成。

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`

## 风险边界

- 不新增视觉模型，不默认启动 detector。
- 不把 queue 命名为 label truth；它只是人工复盘入口。
- 不修改 ROS2 interface 字段，保持诊断 payload 向后兼容。
