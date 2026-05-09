# Sprint 2026.05.10_01-02 Final

## 收口结论

本轮围绕 Objective 5 远程诊断推进，并按当前 delivery MVP 初衷移除早期散落垃圾视觉检测默认链路，软件侧已收口。

operator gateway 现在提供 `/api/diagnostics`，可让手机页面、4G 云桥或远程支持工具拿到软件版本、地图/路线版本、最新状态、最近任务、失败字段、日志引用和可选视觉样本 manifest 引用。

本轮还把 diagnostics payload 组装拆成无 ROS 依赖的纯函数并补行为测试；`trash_detector` 已从代码、launch 和测试门禁中移除，避免把“机器人自己找散落垃圾”误认为当前用户装载送达 MVP 的默认能力。

## 本轮 OKR 进度

| Objective | 当前状态 | 说明 |
| --- | --- | --- |
| Objective 1 硬件控制层 | 软件侧较稳，HIL 未完成 | 本轮未改硬件；仍需 Docker/Humble 和真机串口/运动证据。 |
| Objective 2 送垃圾任务闭环 | 中高进度 | 终态、失败码和 task record 现在更容易被 diagnostics 消费。 |
| Objective 3 导航与固定路线 | 中等偏高 | 本轮未直接改导航；fixed-route status 可继续进入诊断链。 |
| Objective 4 感知模块 | 范围收敛 | 当前 MVP 不发布默认 detector；`TrashStatus` 和视觉 manifest 仅保留为未来可选能力边界。 |
| Objective 5 手机用户体验/量产边界 | 中等偏高 | 诊断包入口、payload fallback 测试与手机/喇叭提示词合同落地；完整手机 UI 和量产硬件表仍待实现。 |

## 验证结果

| 命令 | 结果 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` | 24 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge_static.py` | 24 tests OK |
| `python -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_vision/test/test_perception_docs_static.py` | 17 tests OK |
| `bash scripts/run_smoke_tests.sh` | interfaces 6 + hardware 14 + nav 20 + bringup 8 + behavior 96 + vision 1 tests OK |
| `git diff --check -- <本轮关键文件>` | passed |

## 剩余事项

1. Objective 5：把 `/api/diagnostics` 展示成更清晰的手机页面，而不只是 JSON/按钮。
2. Objective 5：补量产硬件约束表和普通用户验收标准。
3. Objective 4：如后续恢复视觉能力，需要新建明确的 perception/data-capture 节点、launch flag、样本 contract 和真实摄像头验证。
4. Objective 1/3：恢复 Docker/Humble build gate，补 HIL、真实摄像头和 Nav2 实跑证据。
5. 全仓 `git diff --check` 仍受既有 CRLF 行尾改动影响；本轮关键文件 scoped diff check 已通过。
