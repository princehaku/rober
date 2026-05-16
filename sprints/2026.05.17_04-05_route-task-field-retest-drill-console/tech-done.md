# Sprint 2026.05.17_04-05 Route Task Field Retest Drill Console - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_drill_console` 的 PC / Robot / mobile 三端 software proof。证据边界固定为 `software_proof_docker_route_task_field_retest_drill_console_gate`，不是真实 route/elevator field pass、HIL、真实手机/browser、dropoff/cancel completion 或 delivery success。

### Autonomy Algorithm Engineer

实际落地：

- 新增 `pc-tools/evidence/route_task_field_retest_drill_console.py`。
- 新增 `pc-tools/evidence/test_route_task_field_retest_drill_console.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。

产出：dependency-free PC gate 消费 `route_task_field_retest_operator_drill` artifact / summary / wrapper / nested JSON，输出 `trashbot.route_task_field_retest_drill_console.v1` 与 `trashbot.route_task_field_retest_drill_console_summary.v1`。summary 包含 console status、safe `evidence_ref`、material pack / result intake / result reconciliation command labels、safe checklist、missing material prompts、operator callback checklist、rerun notes、not-proven 列表和 evidence boundary；缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、弱类型 same-ref、unsafe copy、success/control claim 均 fail closed。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_drill_console.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_drill_console.py
Ran 5 tests in 0.019s OK

python3 pc-tools/evidence/route_task_field_retest_drill_console.py --help
PASS

required rg
PASS

git diff --check -- pc-tools/evidence/route_task_field_retest_drill_console.py pc-tools/evidence/test_route_task_field_retest_drill_console.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
PASS
```

### Robot Platform Engineer

实际落地：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

产出：Robot diagnostics 新增 `route_task_field_retest_drill_console` / `_summary` metadata-only consumer，支持 direct artifact、summary wrapper、Robot-compatible summary、nested `diagnostics.summary` / `diagnostics.diagnostics_summary`。输出只保留 safe summary、safe `evidence_ref`、console status、command labels、safe checklist、missing material prompts、operator callback checklist、boundary、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`；不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL 或 delivery success。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 128 tests in 0.181s OK

required rg
PASS

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
PASS
```

### User Touchpoint Full-Stack Engineer

实际落地：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `docs/product/mobile_user_flow.md`。

产出：mobile/web 新增只读“现场复测演练控制台” panel，消费 `route_task_field_retest_drill_console` artifact / summary / Robot diagnostics compatible summary，展示 console status、safe `evidence_ref`、safe checklist/copy、command labels、missing material prompts、operator callback checklist、boundary、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。Copy/export 只从后端 `safe_copy` 生成 whitelist-only JSON；Start Delivery / Confirm Dropoff / Cancel gating 不变，未新增 ACK、cursor 或 robot command 请求。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 30 tests in 0.073s OK

node --check mobile/web/app.js
PASS

required rg
PASS

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
PASS
```

## 2. 主会话集成验收

主会话只做范围和证据核对，未直接修改工程实现文件。

```text
git status --short --branch
PASS: 只看到本轮计划、PC gate、Robot diagnostics、mobile/web、接口/产品/导航文档改动。

rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|trashbot.route_task_field_retest_drill_console" ...
PASS: PC、Robot、mobile、docs、sprint planning 均命中。

git diff --check -- 本轮 touched files
PASS
```

## 3. OKR 判断

- Objective 2：从约 86% 保守上调到约 87%。理由是 field retest operator drill 已推进为可被 PC、Robot diagnostics 和 mobile 共同消费的 drill console，能把门状态、目标楼层、人工协助、dropoff/cancel completion 和 delivery result 的下一步回填清单更稳定地串到同一 `evidence_ref`；仍不是 field pass。
- Objective 3：从约 86% 保守上调到约 87%。理由是 material pack / result intake / result reconciliation 的 command labels、safe checklist、missing prompts 和 callback checklist 已形成 console summary，真实 Nav2/fixed-route runtime log、route completion signal、task record 的现场回填路径更清晰；仍不是真实 Nav2/fixed-route 实跑。
- Objective 4：从约 97% 保守上调到约 98%。理由是 mobile/web 新增 phone-safe “现场复测演练控制台”解释层，现场支持能看懂 console status、safe checklist/copy、缺失材料和边界，且主操作 gating 未改变；仍不是真实手机/browser 或 production app proof。
- Objective 1：保持约 77%。本轮没有真实 WAVE ROVER、UART、2D LiDAR、ToF、HIL-entry、`T=1001` feedback、`/odom`、`/imu/data` 或 `/battery`。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 或其他外部 O5 材料。

## 4. 剩余风险

- 真实 route/elevator field materials 仍缺：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 真实 WAVE ROVER、2D LiDAR、ToF、UART、HIL-entry 和 HIL 仍缺。
- 真实手机/browser、production app、真实 PWA prompt/user choice 仍缺。
- Objective 5 external proof 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 本轮所有结果必须继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
