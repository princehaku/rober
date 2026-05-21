# Cloud ACK Lookup Pending Status Guard Tech Done

Run time: 2026-05-21 22:21 CST

## Sprint Type

- sprint_type: epic
- capability: `cloud_ack_lookup_pending_status_guard`
- degraded_state: `ack_lookup_pending`
- ack_semantics: `ack_lookup_pending_not_delivery_success`
- evidence_boundary: `software_proof_docker_cloud_ack_lookup_pending_status_guard`

## 用户价值和产品北极星

用户价值：手机查询 command ACK 时，如果 ACK 还不存在，用户看到的是“机器人尚未处理该命令；继续等待或联系支持”，而不是失败完成、送达成功或可继续下发主操作。

产品北极星：普通手机用户不需要理解 ACK、cursor、ROS topic 或云端内部错误，也能判断当前是否可以继续操作；缺 ACK 时只能等待或走支持路径，主操作保持 fail closed。

## OKR 映射

- Primary: Objective 5 KR1 / KR6，云中转 commands/status/ack contract 与 graceful degradation。
- Supporting: Objective 4 KR1 / KR5 / KR7，手机端主操作安全、用户可理解状态和支持诊断。
- Boundary: Objective 1 / 2 / 3 不因本 sprint 增加进度；本 sprint 不提供硬件、路线、电梯、HIL、真实手机、真实云或 delivery proof。

Objective 5 仍约 68%，Objective 1 仍约 81%，O2/O3/O4 仍约 99%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser proof 或 delivery success，因此 OKR 百分比不提高。

## KR 拆解或更新

- KR5.1 已完成软件证明：`GET /robots/{robot_id}/commands/{command_id}/ack` missing ACK 仍保持 `404` / `ack_not_found`，并补充 canonical `remote_readiness`。
- KR5.2 已完成软件证明：`remote_readiness` 包含 `capability=cloud_ack_lookup_pending_status_guard`、`degradation_state=ack_lookup_pending`、`ack_semantics=ack_lookup_pending_not_delivery_success`、`proof_boundary=software_proof_docker_cloud_ack_lookup_pending_status_guard`。
- KR5.3 已完成软件证明：mobile/web 渲染 `ack_lookup_pending`，Start Delivery / Confirm Dropoff / Cancel 保持 disabled，Diagnostics / Support Handoff 保持 visible。
- KR5.4 已完成证据边界：全链路保留 `remote_ready=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`，不把 missing ACK 写成送达成功。

## 本轮核心抓手

本轮把 missing ACK lookup 从 plain `ack_not_found` 归一为命名 fail-closed pending state：

- `cloud_ack_lookup_pending_status_guard`
- `ack_lookup_pending`
- `ack_lookup_pending_not_delivery_success`
- `software_proof_docker_cloud_ack_lookup_pending_status_guard`

## 实际改动

Robot/API worker delivered:

- Missing ACK lookup remains `404` / `ack_not_found`.
- Response now includes canonical `remote_readiness` with `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `retry_hint=continue_polling_or_contact_support`.
- Diagnostics gained the safe alias for `robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary`.
- Related docs were synchronized in `docs/product/remote_4g_mvp.md` and `docs/interfaces/operator_gateway_diagnostics.md`.

Full-Stack worker delivered:

- `mobile/web` renders the `ack_lookup_pending` state with phone-safe copy.
- Start Delivery / Confirm Dropoff / Cancel remain disabled.
- Diagnostics / Support Handoff remain visible.
- Fixture and mobile flow docs were synchronized in `mobile/web/fixtures/robot_diagnostics_cloud_ack_lookup_pending_status_guard.json` and `docs/product/mobile_user_flow.md`.

Hardware consultation delivered:

- Read-only review confirmed this sprint makes no WAVE ROVER, UART, serial, voltage, 2D LiDAR, ToF, HIL, real-material, or PR #5 resolution claim.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending.
- Comment `3269642220` remains only software-proof publication, not reviewer resolution.

Product closeout delivered:

- Updated this sprint closeout chain.
- Updated `OKR.md` 4.1 to this sprint/time with conservative evidence boundary.
- Appended `docs/process/okr_progress_log.md` entry.

## 验证结果

Robot/API worker:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 320 tests in 29.185s
OK

required rg passed
scoped git diff --check passed
```

Full-Stack worker:

```text
node --check mobile/web/app.js
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 229 tests in 1.800s
OK

fixture JSON parse passed
required rg passed
scoped git diff --check passed
```

Hardware consultation:

```text
test -f docs/vendor/VENDOR_INDEX.md
passed

required rg hit OKR/production boundary
no file changes
```

Product closeout verification is recorded in `final.md`.

## 偏差

No product-scope deviation. Engineering workers updated product/interface docs outside this Product closeout scope before closeout; Product only changed sprint/OKR/progress-log files.

## 剩余风险

- No real public HTTPS/TLS.
- No 4G/SIM.
- No OSS/CDN live traffic.
- No production DB/queue.
- No production worker/cutover.
- No true phone/browser proof.
- No WAVE ROVER/UART/HIL or real hardware material.
- No route/elevator field pass.
- No dropoff/cancel completion, delivery result, or delivery success.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending; comment `3269642220` is only software-proof publication.

## 需要做什么

下一步若继续 O5，必须优先拿真实 external evidence：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser proof。若这些仍不可用，不应继续用本地 metadata wrapper 提高 O5；应转向 O1 真实硬件材料 / HIL 或 O2/O3/O4 真实 field evidence。

## 优先级和验收口径

P0 control-plane safety accepted for Docker/local software proof only:

- Missing ACK cannot be interpreted as delivery success.
- Primary phone actions remain disabled.
- Diagnostics/support remain available.
- Evidence boundary remains `software_proof_docker_cloud_ack_lookup_pending_status_guard`.
- OKR percentages remain unchanged.

## 对应责任 Engineer

- Robot Platform Engineer: Robot/API ACK lookup contract, diagnostics normalization, Python tests, interface/product docs.
- User Touchpoint Full-Stack Engineer: mobile/web rendering, fixture, UI tests, mobile product docs.
- Hardware Infra Engineer: read-only vendor / PR #5 / hardware boundary consultation.
- Product Manager / OKR Owner: closeout, OKR wording, progress log, evidence boundary.
