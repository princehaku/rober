# O6 Worker Report

## 实际改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 实现内容

- O6 `same_task_route_execution_material_packet` 回读摘要新增并保留 5 个 credit-aware 字段：
  - `live_or_field_command_evidence_present`
  - `delivery_or_operator_material_consumed`
  - `route_execution_credit_candidate`
  - `credit_support_only_reason`
  - `credit_required_evidence`
- 对缺 credit 字段、错误类型、credit candidate 与布尔条件不一致等情况做 section-local fail-closed，降级为 `blocked_not_proven`。
- 固定保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，即使 `route_execution_credit_candidate=true` 也不放开。
- 单测补充正向保留、consumer 回读和缺 credit 字段 fail-closed 断言。
- 接口文档同步补充 O6 对 credit-aware 字段的保留范围与 fail-closed 规则。

## 验证结果

```bash
$ python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# exit 0

$ python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
.....................................................................
----------------------------------------------------------------------
Ran 171 tests in 68.289s

OK

$ git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
# exit 0
```

## 失败定位

- 本轮验收命令均通过，无新增失败待定位项。

## 剩余风险

- 当前只验证 O6 archive/readback 的软件安全摘要，不证明真实 production cloud、真实 live Nav2、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- `route_execution_credit_candidate=true` 目前仍只是 credit-aware 材料满足的软件判断，不应被上层解释为控制权限或交付成功。
