# Cloud Poll Backoff Rate Limit Guard Final

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard`
- Closeout time: 2026-05-21 06:26 Asia/Shanghai
- Evidence boundary: `software_proof_docker_cloud_poll_backoff_rate_limit_guard`

## 最终结论

本 sprint 完成 Objective 5 的 `cloud_poll_backoff_rate_limit_guard` Docker/local software proof：Robot outbound polling 在 repeated poll failure / empty-poll pressure 下进入 bounded backoff/rate-limit 状态；operator gateway diagnostics/status 和 mobile/web 都能看到同一个 fail-closed `cloud_poll_backoff`，并保持主操作 disabled。

核心用户价值是：弱网或重试窗口内，普通手机用户看到的是"等待退避窗口"而不是含混的失败或成功状态；Start Delivery / Confirm Dropoff / Cancel 不会因为云轮询压力被误启用。

## 实际改动文件

Robot Platform Engineer:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/operator_gateway_diagnostics.md`

User Touchpoint Full-Stack Engineer:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product Manager / OKR Owner:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/tech-done.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/side2side_check.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/final.md`

## 验证结果

Robot worker:

```text
py_compile passed
focused unittest: Ran 437 tests in 99.553s OK
required rg passed
scoped git diff --check passed
```

Full-Stack worker:

```text
node --check mobile/web/app.js passed
mobile unittest: Ran 197 tests ... OK
JSON fixture check passed
required rg passed
scoped git diff --check passed
```

Product closeout:

```text
test -f tech-done.md / side2side_check.md / final.md passed
required rg passed
scoped git diff --check passed
```

## 失败定位

Robot worker 首轮发现 diagnostics wrapper 会从 raw status 重算 `phone_readiness` 并保留 unsafe `safe_phone_copy`。根因是 `cloud_poll_backoff` 进入 `phone_readiness.remote_readiness` 时没有走同一 sanitation 路径。修复后，`phone_readiness.remote_readiness` 对 `cloud_poll_backoff` 使用 safe sanitized summary，最终 focused Robot unittest 通过。

Product closeout 没有发现新增文件缺失、required marker 缺失或 closeout diff whitespace 问题。

## OKR 更新

- Objective 5 保持约 68%。本轮只证明 `software_proof_docker_cloud_poll_backoff_rate_limit_guard`，不是 real external cloud proof，不能提高完成度。
- Objective 1 保持约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending。
- Objective 2/3/4 保持约 99%。本轮没有真实 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion、delivery result、true phone/browser proof 或 delivery success。

## 风险、阻塞和证据链

仍缺的真实证据：

- real public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue connectivity
- production worker/migration/cutover
- true phone/browser proof
- real iPhone/Android device behavior
- WAVE ROVER/UART/HIL
- PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution and real 2D LiDAR / ToF materials
- real Nav2/fixed-route runtime log
- route/elevator field pass
- dropoff/cancel completion
- delivery result and delivery success

本轮状态必须继续保留：

- `remote_ready=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `retry_hint=wait_for_backoff_window`
- `source=software_proof`
- `not_proven`

## 提交建议

建议主会话提交并推送，但只在统一纳入 Robot、Full-Stack 和 Product closeout 全部文件后提交。提交说明应明确这是 `software_proof_docker_cloud_poll_backoff_rate_limit_guard`，不要写成真实公网云、真实 4G、真实手机、HIL、route/elevator field pass、delivery success 或 PR #5 resolved。
