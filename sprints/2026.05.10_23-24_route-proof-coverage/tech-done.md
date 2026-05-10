# Sprint 2026.05.10 23-24 Route Proof Coverage - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-11 00:18 Asia/Shanghai
- 实现 owner：`autonomy-engineer`、`full-stack-software-engineer`
- 收口方式：基于两位工程子 agent 已完成实现与验证证据做文档收口（本轮 Product 不执行长命令）

## 本轮实际改动（按 owner）

### 1) Objective 3 主切片：route proof coverage（`autonomy-engineer`）

改动文件：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_proof_summary.py`（新增）
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- `src/ros2_trashbot_nav/test/test_route_proof_summary.py`（新增）
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`
- `docs/navigation/fixed_route_workflow.md`

结果摘要：

- fixed-route status 增强了 `route_proof_summary` 结构化字段（coverage、missing checkpoints、gate status、last block reason）。
- 文档补齐了 route proof 字段口径与稳定性规则。
- nav 侧提供 coverage source-of-truth，供 behavior/operator 消费，不引入第二口径。

### 2) Objective 3/5 接口触点切片：operator diagnostics route-proof mapping（`full-stack-software-engineer`）

改动文件：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/interfaces/ros_contracts.md`

结果摘要：

- diagnostics 增加 route proof summary 抽取与分类（`ready` / `waiting_visual_gate` / `insufficient_coverage` / `blocked` / `unknown`）。
- operator 页能消费同一 route proof contract 并给出可读阻塞原因。
- 接口文档明确“behavior 只映射不重算 coverage”。

## 验证证据（子 agent 回传）

1. nav tests：通过
   - 关键输出：`Ran 42 tests ... OK`
2. behavior operator tests：通过
   - 关键输出：`Ran 47 tests ... OK`
3. smoke：通过
   - 关键输出：`Ran 127 tests ... OK`
   - 关键输出：`Ran 13 tests ... OK`

说明：以上为两位工程子 agent 实现阶段回传证据；本轮 Product 收口不重复执行 `run_smoke_tests.sh`。

## 偏差与处理

- 无新增功能偏差需要回滚。
- 本轮按约束只做文档收口，不扩展文件范围，不改动范围外代码。

## 剩余风险

1. 本轮仍是软件/离线验证证据，不代表真实 Nav2、真实相机输入或真实 WAVE ROVER 行驶成功。
2. 无 HIL/实机证据（串口、底盘反馈、实车路线采集、实车视觉门控）仍是 Objective 3/1 的关键缺口。
3. route proof 可解释性已提升，但现场可达性仍需后续上车验证闭环。
