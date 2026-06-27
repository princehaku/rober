# 2026-06-27 12:48 upper Nav2 execute strict wheel gate

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `nav2_goal_execution_proven_from_latest_result()`，把上车 `/api/nav2/goal/execute`
    外层回包的 `nav2_goal_execution_proven` 收紧为必须同窗口
    `base_feedback_summary.wheel_feedback_lr_nonzero_proven=true`。
  - 新增 `nav2_goal_execution_not_proven_reasons()`，当 action 已 `goal_succeeded` 但
    wheel raw L/R 未非零时，外层 `not_proven` 明确包含 `wheel_feedback_lr_nonzero`。
  - 外层 `hil_pass` 同步受 strict wheel gate 约束，避免 helper/PC summary 严格而 upper execute
    回包短暂假阳性。
- `onboard/tests/test_upper_robot_api.py`
  - 更新 Nav2 execute 成功测试，要求 wheel L/R 非零材料才能 proven。
  - 新增 action succeeded 但 wheel L/R false 时不 proven 的回归。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 upper execute、O11 helper 和 PC summary 的完整路线证明口径。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 通过，`Ran 62 tests in 0.140s`，`OK`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`
  - 通过。

- 部署到真实上位机 `root@192.168.1.11:37878`
  - 已替换 `/root/rober/onboard/scripts/upper_robot_api.py`，并通过远端
    `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py`。
  - 已重启 8787 upper API，`ss -ltnp` 显示 `0.0.0.0:8787` 由
    `python3 /root/rober/onboard/scripts/upper_robot_api.py ...` 监听。
- 远端纯函数验证：
  - wheel false -> `False`，not_proven 为
    `['wheel_feedback_lr_nonzero', 'delivery_success', 'operator_dropoff_confirmation']`。
  - wheel true -> `True`，not_proven 为
    `['delivery_success', 'operator_dropoff_confirmation']`。
- 远端只读 latest 验证：
  - `GET http://192.168.1.11:8787/api/nav2/goal/execution/latest`
    返回 `latest_status=goal_succeeded`、`nav2_goal_execution_proven=false`、
    `hil_pass=false`、`base_feedback_summary.wheel_feedback_lr_nonzero_proven=false`、
    `base_feedback_summary.sample_count=239`、`nonzero_sample_count=0`、
    `base_command_summary.nonzero_command_observed=true`、`nonzero_command_count=49`。
  - PC 7001 summary 返回 `readback_summary.nav2.status=goal_succeeded_wheel_feedback_not_proven`、
    `goal_execution_base_feedback_lr_nonzero_proven=false`、
    `next_execution_base_command_mode=ros`。

## 剩余风险

- 本轮没有发起新的 NavigateToPose，不证明真实路线已经跑通。
- 当前现场剩余缺口仍是同执行窗口 WAVE ROVER wheel raw L/R 非零；需要现场安全确认后执行下一次
  `base_command_mode=ros` 路线复验。
