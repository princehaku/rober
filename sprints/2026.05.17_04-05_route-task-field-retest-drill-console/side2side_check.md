# Sprint 2026.05.17_04-05 Route Task Field Retest Drill Console - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD / Tech-plan 要求 | 实际结果 | 结论 |
| --- | --- | --- |
| PC gate 消费 `route_task_field_retest_operator_drill` artifact / summary / wrapper / nested JSON | Autonomy worker 新增 `route_task_field_retest_drill_console.py` 和 unittest，输出 artifact / summary schema | 通过 |
| 固定 boundary 与 fail-closed 标志 | PC、Robot、mobile、docs 均保留 `software_proof_docker_route_task_field_retest_drill_console_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| Robot diagnostics metadata-only consumer | Robot worker 新增 `route_task_field_retest_drill_console` / `_summary` consumer，unsupported/unsafe/success/action enabled 均 fail closed | 通过 |
| mobile/web 只读 panel | Full-stack worker 新增“现场复测演练控制台” panel，展示 safe summary，copy/export whitelist-only | 通过 |
| Start / Confirm Dropoff / Cancel gating 不变 | Full-stack worker 验证未新增 Start / Confirm / Cancel / ACK / cursor / robot command 请求 | 通过 |
| 文档同步 | `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 已更新 | 通过 |

## 2. 证据边界核对

本轮只证明 Docker/local software proof：

- PC gate 可生成 drill console artifact / summary。
- Robot diagnostics 可 metadata-only 消费 safe summary。
- mobile/web 可只读展示 phone-safe panel。
- 三端均保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮不证明：

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route runtime。
- 真实 route completion signal 或 task record。
- 真实 dropoff/cancel completion 或 delivery success。
- WAVE ROVER、UART、2D LiDAR、ToF、HIL-entry 或 HIL。
- 真实手机/browser、production app 或 PWA prompt/user choice。
- Objective 5 external proof。

## 3. 验收结果

Worker 验证均通过：

```text
Autonomy: py_compile PASS; unittest Ran 5 tests OK; CLI help PASS; required rg PASS; scoped diff check PASS
Robot: py_compile PASS; diagnostics unittest Ran 128 tests OK; required rg PASS; scoped diff check PASS
Full-stack: mobile unittest Ran 30 tests OK; node --check PASS; required rg PASS; scoped diff check PASS
```

主会话集成核对：

```text
rg route_task_field_retest_drill_console / boundary / schema
PASS

git diff --check -- 本轮 touched files
PASS
```

## 4. 收口判断

本 sprint 达到 PRD / tech-plan 的软件验收口径，可以收口为 `software_proof_docker_route_task_field_retest_drill_console_gate`。不得把本轮写成真实 route/elevator field pass、HIL、真实手机/browser、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
