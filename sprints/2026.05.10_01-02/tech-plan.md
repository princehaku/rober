# Sprint 2026.05.10_01-02 Tech Plan

## 技术方案

1. 在 `OperatorGateway` 增加诊断参数：
   - `software_version`
   - `map_version`
   - `route_version`
   - `log_refs`
   - `vision_sample_manifest_ref`
2. 增加 `OperatorGateway.diagnostics()`：
   - 复用当前 status snapshot。
   - 汇总最近任务、终态失败字段、状态文件引用和诊断引用。
   - 不读取或伪造不存在的日志/样本文件。
3. 在 `operator_gateway_http.make_handler()` 增加 `GET /api/diagnostics`。
4. 更新 HTTP/static 测试和接口/产品文档。

## 验证计划

| 命令 | 目的 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` | 验证本地 operator gateway contract 和 diagnostics payload fallback |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge_static.py` | 验证远程桥状态 contract 未回退 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_vision python3 -m unittest src/ros2_trashbot_vision/test/test_perception_docs_static.py` | 验证当前 MVP 不随包发布默认 detector 的视觉策略文档 |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | 全局软件护栏 |

## 不做事项

- 不改 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压或机械尺寸。
- 不声明真实手机 App、云账号、Docker/Humble build 或 HIL 完成。
- 不一次性改完整前端 UI；本轮先交付可消费诊断 API。
- 不把散落垃圾视觉检测当作当前 delivery MVP 的默认链路；已废弃的 `trash_detector` 不再作为验收项。
