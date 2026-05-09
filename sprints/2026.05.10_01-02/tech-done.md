# Sprint 2026.05.10_01-02 Tech Done

## 状态

- 当前阶段：TECH-DONE。
- 本次交付：Objective 5 远程诊断最小数据包；同时按 MVP 初衷移除早期 `trash_detector` 默认感知链路。
- 主责 owner：`User Touchpoint Full-Stack Engineer`，由 `Autonomy Algorithm Engineer` 补视觉样本证据边界。

## 实际改动

| 文件 | 改动 |
| --- | --- |
| `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py` | 增加 diagnostics 参数，`/api/diagnostics` 复用 status snapshot 并输出软件版本、地图/路线版本、最近任务、失败字段、日志引用、视觉 manifest 引用和 status 文件引用。 |
| `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` | 新增无 ROS 依赖的 diagnostics payload 组装函数，覆盖 failure fallback 和 `log_refs` 归一化。 |
| `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py` | 增加 `GET /api/diagnostics` 路由和最小页面按钮。 |
| `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` | 新增 payload 行为测试，验证最新 status 优先、last_task fallback、空 map/route 不伪造文件存在、日志引用归一化。 |
| `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py` / `test_operator_gateway_static.py` | 扩展 HTTP contract 和静态契约测试。 |
| `src/ros2_trashbot_vision/ros2_trashbot_vision/trash_detector.py` | 删除早期 OpenCV/HSV `trash_detector` 节点，当前 delivery MVP 不再随包发布默认散落垃圾检测器。 |
| `src/ros2_trashbot_vision/test/test_trash_detector_static.py` | 删除已废弃 detector 的静态测试。 |
| `src/ros2_trashbot_vision/setup.py` / `package.xml` / `ros2_trashbot_vision/__init__.py` | 移除 `trash_detector` console script 和 detector 专属 OpenCV/cv_bridge/numpy/sensor_msgs 依赖，保留 vision 包作为未来视觉能力边界。 |
| `src/ros2_trashbot_bringup/launch/learn.launch.py` / `bringup.launch.py` / `autonomous.launch.py` | 移除默认启动 `trash_detector` 及其 camera/vision 参数，避免 MVP launch 启动不存在或不符合当前初衷的节点。 |
| `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py` | 移除对 `/trashbot/vision/trash_detected` 的订阅和巡逻记录散落垃圾点的旧逻辑，delivery MVP 只依赖用户装载、导航和投放确认。 |
| `AGENTS.md` / `OKR.md` / `.codex/agents/registry.toml` / `.codex/agents/autonomy-engineer.toml` | 同步收敛组织和 OKR 口径：当前 MVP 不默认发布散落垃圾 detector，视觉感知是未来可选能力。 |
| `docs/interfaces/ros_contracts.md` | 记录 `/api/diagnostics` 和 diagnostics 参数合同。 |
| `docs/product/mobile_user_flow.md` | 记录最小诊断 API 和手机/喇叭状态提示合同。 |
| `docs/vision/perception_upgrade_evaluation.md` / `docs/vision/trash_status_contract.md` | 记录当前 MVP 不发布默认 detector；`TrashStatus` 和视觉样本 manifest 只保留为未来可选感知能力边界。 |
| `scripts/run_smoke_tests.sh` | 修复 CRLF 导致 bash 将 `pipefail\r` 解析为非法参数的问题，恢复 WSL/Linux smoke gate。 |

## 验证结果

| 命令 | 结果 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` | passed，24 tests OK |
| `python -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_vision/test/test_perception_docs_static.py` | passed，17 tests OK |
| `bash scripts/run_smoke_tests.sh` | passed，interfaces 6、hardware 14、nav 20、bringup 8、behavior 96、vision 1 |

## 完成前反思

- 需求是否满足：Objective 5 KR4 已有可消费 diagnostics payload；早期 `trash_detector` 已从当前 MVP 默认链路移除，避免与“用户装载后送达投放点”的产品初衷冲突。
- 是否误改硬件事实：本轮未新增 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压或机械尺寸结论。
- 是否留下 TODO：本轮未新增代码 TODO。
- 验证缺口：未运行 Docker/Humble `colcon build`，未做真实手机浏览器、摄像头、Nav2 或 WAVE ROVER HIL。

## 剩余风险

- `/api/diagnostics` 仍是 API 和极简浏览器入口，不是完整手机 App。
- `vision_sample_manifest_ref` 仍是可配置诊断字段，但当前代码不再默认生产视觉样本 manifest。
- Objective 4 未来如恢复视觉能力，需要新建明确的 perception/data-capture 节点、launch flag、样本 contract 和真实摄像头验证。
- Docker/Humble 与 HIL 仍是 Objective 1/3 的主要验收缺口。
