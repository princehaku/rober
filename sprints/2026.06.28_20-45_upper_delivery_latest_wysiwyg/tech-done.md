# 2026-06-28 20:45 upper delivery latest WYSIWYG

sprint_type: micro

## 实际改动

- 修改 `onboard/scripts/upper_robot_api.py`：`GET /api/delivery/latest` 的只读回包现在把最近 delivery gate artifact 里的 `status`、`missing_required_material`、`required_material`、`nav2_goal_execution`、`operator_report` 提升到顶层。
- 修改 `onboard/tests/test_upper_robot_api.py`：新增 delivery latest 单元测试，锁定缺失材料必须顶层可见，且 `delivery_success/safe_to_control/robot_control_executed` 仍为 false。
- 更新 `docs/product/pc_tools_workstation.md`：记录 8787 直连 delivery latest 的所见即所得口径。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_delivery_latest_lifts_missing_material_to_top_level`，结果 `1 test OK`。
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，结果 `81 tests OK`。
- 通过：部署到上车 8787 后只读复核 `GET http://192.168.1.11:8787/api/delivery/latest`，结果顶层 `status=blocked_missing_delivery_material`、`proof_state=not_proven`、`delivery_success=false`、`missing_required_material=[confirm_delivery_completion, operator_report_ready_for_review, operator_observed_motion, operator_observed_stop, structured_hil_claims.delivery_success]`、`nav2_goal_execution.status=goal_succeeded`、`operator_report.operator_report_status=unsafe_or_incomplete`、`safe_to_control=false`、`robot_control_executed=false`。
- 通过：PC 7001 只读复核 `GET /api/robot-control/delivery/latest?baseUrl=http://192.168.1.11:8787`，结果 `proxy_status=latest_loaded`，`missing_required_material` 与 8787 顶层一致。

## 剩余风险

- 本轮只修 delivery latest 的读回合同，不实际提交送达确认，不生成 delivery success。
- 真实 delivery success 仍需要新一轮路线执行后 wheel raw L/R 非零、现场 motion/stop 观察和 operator delivery claim。
