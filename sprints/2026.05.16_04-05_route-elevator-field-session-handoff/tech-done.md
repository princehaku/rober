# Sprint 2026.05.16_04-05 Route Elevator Field Session Handoff - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 Product Closeout 收口三个 Engineer Task，证据边界统一为 `software_proof_docker_route_elevator_field_session_handoff_gate`。该边界只证明 Docker/local 软件环境中，PC route debug console、route completion signal、elevator-route reconciliation 可以被整理成同一 `evidence_ref` 的现场交接 artifact/summary，并被 Robot diagnostics 与 mobile/web 只读消费。

### Task A - Autonomy Algorithm Engineer

改动文件：

- `pc-tools/evidence/route_elevator_field_session_handoff.py`
- `pc-tools/evidence/test_route_elevator_field_session_handoff.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

完成内容：

- 新增 `route_elevator_field_session_handoff` CLI。
- 输出 artifact `schema=trashbot.route_elevator_field_session_handoff.v1`。
- 输出 summary `schema=trashbot.route_elevator_field_session_handoff_summary.v1`。
- 固定 `evidence_boundary=software_proof_docker_route_elevator_field_session_handoff_gate`。
- 保留 `same_evidence_ref_required=true`、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。
- 缺输入、坏 schema、unsafe copy、success claim 或 evidence ref mismatch 均 fail closed。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_elevator_field_session_handoff.py pc-tools/evidence/test_route_elevator_field_session_handoff.py
exit 0

PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_elevator_field_session_handoff.py
Ran 8 tests in 0.036s
OK

python3 pc-tools/evidence/route_elevator_field_session_handoff.py --help
exit 0

required rg
exit 0

git diff --check -- pc-tools/evidence/route_elevator_field_session_handoff.py pc-tools/evidence/test_route_elevator_field_session_handoff.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
exit 0
```

### Task B - Robot Platform Engineer

改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

完成内容：

- diagnostics 新增 `route_elevator_field_session_handoff` 与 summary alias metadata-only 消费。
- 支持 artifact/summary schema。
- 缺失、unsafe copy、success claim、`primary_actions_enabled=true` 或 `delivery_success=true` 均 fail closed。
- 不触发 `/api/collect`、ACK、cursor、Nav2、dropoff/cancel、route execution 或 HIL。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 83 tests in 0.082s
OK

required rg
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
exit 0
```

### Task C - User Touchpoint Full-Stack Engineer

改动文件：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

完成内容：

- mobile/web 新增只读“路线电梯现场交接” panel。
- 从 status/diagnostics 中读取 `route_elevator_field_session_handoff*`。
- 展示 handoff verdict、safe `evidence_ref`、same-evidence-ref、required materials、operator next steps、boundary、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。
- Start / Confirm Dropoff / Cancel gating 未改变。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
Ran 47 tests in 0.161s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit 0

node --check mobile/web/app.js
exit 0

required rg
exit 0

git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
exit 0
```

## 2. Product Closeout 判断

用户价值：现场同学现在有一层同一 `evidence_ref` 的 route + elevator field-session handoff，可以知道下一次真实现场 session 需要补齐哪些材料，并把 PC console、route completion signal、电梯复账、Robot diagnostics 和 mobile/web 只读解释连在一起。

OKR 映射：

- Objective 2：支持 KR5、KR6、KR7，现场回填清单覆盖电梯门状态、目标楼层确认、人工协助记录、task record、completion signal、dropoff/cancel completion 和 delivery result。
- Objective 3：支持 KR3、KR4、KR5，固定路线复盘链路从 PC console 同屏复账推进到现场 session handoff。
- Objective 5：不推进。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

本轮核心抓手已完成：handoff artifact/summary、Robot metadata-only consumption、mobile read-only panel 三段闭合，且全部保留 `delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。

## 3. 偏差与风险

无工程返工偏差。Product Closeout 没有改工程代码，也没有扩大测试范围。

剩余风险：

- 本轮不是真实 route/elevator field pass。
- 不证明真实 Nav2/fixed-route、真实路线采集、真实电梯门状态、真实目标楼层确认、真实人工协助、真实手机/browser、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、真实 delivery success 或 Objective 5 external proof。
- 下一轮如果要继续提高 O2/O3，需要真实现场材料沿同一 `evidence_ref` 回填，而不是再增加本地-only handoff 包装。

## 4. Closeout 验收命令

Product Closeout 需要继续运行：

```bash
rg -n "route_elevator_field_session_handoff|software_proof_docker_route_elevator_field_session_handoff_gate|Objective 2|Objective 3|Objective 5|not real|不证明|delivery_success=false" sprints/2026.05.16_04-05_route-elevator-field-session-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_04-05_route-elevator-field-session-handoff OKR.md docs/process/okr_progress_log.md
```
