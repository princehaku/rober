# Cloud Poll Backoff Rate Limit Guard Tech Done

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard`
- Closeout time: 2026-05-21 06:26 Asia/Shanghai
- Evidence boundary: `software_proof_docker_cloud_poll_backoff_rate_limit_guard`
- Product owner: `product-okr-owner`
- Engineering owners: `robot-software-engineer`, `full-stack-software-engineer`

## 用户价值和产品北极星

普通手机用户不应该理解云轮询、退避窗口、ACK 或 Docker 证明边界。弱网或高频空轮询场景下，产品要把远程控制明确降级为等待重试窗口，并保持 Start Delivery、Confirm Dropoff、Cancel 不可用，避免用户把重试中状态误解成送达成功。

本轮核心抓手是把 repeated poll failure / empty-poll pressure 转成同一个 fail-closed 状态：

- `degradation_state=cloud_poll_backoff`
- `remote_ready=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `retry_hint=wait_for_backoff_window`
- `proof_boundary=software_proof_docker_cloud_poll_backoff_rate_limit_guard`

## OKR 映射与 KR 拆解

- Objective 5 / KR1：补强 command/status/ack 控制面轮询退避与限频状态，不暴露 `/cmd_vel` 或 inbound robot control。
- Objective 5 / KR6：把 repeated poll failure / empty-poll pressure 归类为 graceful degradation，可恢复但 fail-closed。
- Objective 4：手机端能展示中文安全文案，并持续禁用主操作。
- Objective 1：无进度提升；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending。
- Objective 2/3：无 route/elevator、Nav2/fixed-route、dropoff/cancel、delivery result 或 field pass claim。

## 实际改动

Robot Platform Engineer 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/operator_gateway_diagnostics.md`

Robot 侧产出：

- `RemoteBridgeWorker` 增加 bounded poll pressure / backoff tracking。
- operator gateway status / diagnostics 增加 `cloud_poll_backoff` safe readiness 和 `robot_diagnostics_cloud_poll_backoff_rate_limit_guard_summary`。
- 保持 auth failure、media degraded、cloud unreachable、malformed response、expired command、duplicate/conflict、sequence regression、pending ACK 等更具体 O5 状态的优先级。
- 修复首轮 diagnostics failure：`phone_readiness` 曾从 raw status 重新计算并保留 unsafe `safe_phone_copy`；现已在 `phone_readiness.remote_readiness` 内 sanitizing `cloud_poll_backoff`。

User Touchpoint Full-Stack Engineer 已完成：

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Full-Stack 侧产出：

- 既有 cloud readiness panel 消费 `cloud_poll_backoff`。
- 手机端展示等待 retry/backoff window 的中文文案。
- Start Delivery / Confirm Dropoff / Cancel 保持 disabled。
- 增加 fixture 和 focused mobile tests。

Product Manager / OKR Owner 已完成 closeout：

- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/tech-done.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/side2side_check.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Robot worker validation:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ... passed
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 437 tests in 99.553s OK
required rg passed
scoped git diff --check passed
```

Full-Stack worker validation:

```text
node --check mobile/web/app.js passed
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 197 tests ... OK
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json passed
required rg passed
scoped git diff --check passed
```

Product closeout validation is recorded in `final.md`.

## 偏差与失败定位

- Robot worker 首轮 diagnostics 路径发现 `phone_readiness` 从 raw status 重新计算后保留 unsafe `safe_phone_copy`。定位为 wrapper sanitation 边界不一致，已修复为在 `phone_readiness.remote_readiness` 中对 `cloud_poll_backoff` 做 safe sanitation，并通过 focused unittest 回归。
- Product closeout 未改工程代码或测试，未运行 Robot/Full-Stack 的实现测试重跑；本文件采用 worker 已返回的验证证据，并额外运行 closeout 文件/rg/diff checks。

## 剩余风险与非证明边界

本轮只能关闭为 `software_proof_docker_cloud_poll_backoff_rate_limit_guard`。它不是 real external cloud proof，也不是：

- real public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- production worker/cutover
- true phone/browser proof
- HIL
- route/elevator field pass
- delivery success
- PR #5 reviewer resolution

Objective 5 保持约 68%，没有百分比提升。Objective 1 保持约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending。Objective 2/3/4 保持约 99%。
