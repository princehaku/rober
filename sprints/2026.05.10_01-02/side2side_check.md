# Sprint 2026.05.10_01-02 Side To Side Check

## 文档阶段门禁

- 前置文档：`tech-done.md`。
- 当前阶段：SIDE TO SIDE CHECK。
- 本阶段完成条件：对照 PRD、OKR、接口、验证证据和风险边界。

## PRD vs 实现

| PRD 项 | 实现状态 | 证据 | 结论 |
| --- | --- | --- | --- |
| `GET /api/diagnostics` 返回 JSON | implemented | `test_diagnostics_endpoint_returns_remote_support_package` | closed |
| 包含软件版本、地图/路线版本 | implemented | `software_version`、`map_version`、`route_version` 参数和 diagnostics payload 测试 | closed |
| 包含最近任务、失败字段、日志、视觉样本引用 | implemented | `latest_status`、`last_task`、`failure`、`log_refs`、`vision_sample_manifest_ref`，且覆盖 latest-status 优先和 last-task fallback | closed |
| 手机/语音提示合同 | implemented | `docs/product/mobile_user_flow.md` 状态表 | closed |
| 现有 status/collect/dropoff/cancel 不回退 | preserved | operator + remote 定向测试通过 | closed |

## OKR/KR 对照

| OKR | 本轮检查点 | 状态 |
| --- | --- | --- |
| Objective 1 | 本轮未改硬件协议，不新增硬件结论 | unchanged |
| Objective 2 | 任务终态和失败码更容易被手机/远程诊断消费 | improved |
| Objective 3 | fixed-route 状态可继续进入诊断链 | unchanged |
| Objective 4 | 当前 MVP 不再发布默认散落垃圾 detector；视觉 contract 仅保留为未来可选能力边界 | clarified |
| Objective 5 | 远程诊断最小数据包、payload fallback 测试和提示词合同落地 | improved |

## 验证证据

| 命令 | 状态 | 摘要 |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` | passed | 24 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge_static.py` | passed | 24 tests OK |
| `python -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_vision/test/test_perception_docs_static.py` | passed | 17 tests OK |
| `bash scripts/run_smoke_tests.sh` | passed | interfaces 6、hardware 14、nav 20、bringup 8、behavior 96、vision 1 |
| `git diff --check -- <本轮关键文件>` | passed | 本轮关键文件无 whitespace error |

## 风险边界

- 本轮没有新增硬件、串口、WAVE ROVER、ESP32、Orange Pi、电压、引脚、机械尺寸结论。
- Docker/Humble build 和 HIL 未作为完成声明。
- 本轮 diagnostics 是 API 合同和最小页面入口，不是完整手机 App。
- 当前代码不再默认生产视觉样本 manifest；`vision_sample_manifest_ref` 仅保留为未来部署可选引用。
- 全仓 `git diff --check` 仍受既有 CRLF 行尾改动影响，未作为本轮通过声明。

## 本阶段结论

PRD 的软件接口、文档验收和全局 smoke 护栏已 closed。可进入 `final.md`。
