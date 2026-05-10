# Sprint 2026.05.10 09-10 Tech Done

## 实际改动

- `operator_gateway_diagnostics.summarize_vision_manifest()` 新增 `event_counts`、`review_queue_count` 和 bounded `review_queue`。
- review queue 优先暴露 anomaly、route_keyframe、低置信度检测和未复核样本；每项包含 sample ref、context、event type、detection count、max confidence 和 reason。
- 手机 operator diagnostics panel 新增 review queue 数量和下一条待复核样本展示。
- `docs/vision/perception_upgrade_evaluation.md` 明确 review queue 是人工复盘入口，不是 label truth 或模型可生产证据。
- `OKR.md` 更新当前快照和第 19 轮进度，Objective 4 从约 58% 推进到约 61%，Objective 5 从约 67% 推进到约 68%。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py` 直接运行时失败，原因是未设置本地源码 `PYTHONPATH`，无法导入 `ros2_trashbot_behavior`。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py` 通过，23 tests OK。
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 26、bringup 9、behavior 105、vision 8。
- `git diff --check` 通过。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，`docker` 命令不可用，无法完成 Docker/Humble colcon build。

## 偏差与风险

- 本轮不新增视觉模型，不默认启动 detector，不声明已有真实相机数据集。
- review queue 基于 manifest 元数据生成，不读取 companion JSON 或图片内容。
- team 复查提出两个高价值后续：Objective 4 的 `route_data_recorder` callback runtime-style 文件写入验证，以及 Objective 2/3 的 fixed-route dry-run status 到 `TrashCollection` action 集成证明。
