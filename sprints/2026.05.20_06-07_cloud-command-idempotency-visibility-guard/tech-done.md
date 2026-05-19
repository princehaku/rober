# Sprint 2026.05.20_06-07 Cloud Command Idempotency Visibility Guard - Tech Done

## 1. Sprint 状态

- sprint_type: epic
- 主题：`cloud_command_idempotency_visibility_guard`
- 收口时间：2026-05-20 06:21 Asia/Shanghai
- 证据边界：`software_proof_docker_cloud_command_idempotency_visibility_guard`

## 2. 实际改动

### Robot Platform Engineer

- 改动 remote bridge/operator contract，让 duplicate command cached ACK 显式输出 `command_duplicate_deduped`、`duplicate_command_id`、`cached_ack_state`、`ack_semantics=duplicate_cached_ack_not_delivery_success`、`remote_ready=false`、`primary_actions_enabled=false` 和 `proof_boundary=software_proof_docker_cloud_command_idempotency_visibility_guard`。
- duplicate command 不重复提交本地 action；expired duplicate 仍保持 `command_expired` 优先级；pending terminal ACK 仍先阻塞 command pulling。
- 同步 Robot/operator diagnostics focused tests 和 `docs/product/remote_4g_mvp.md` 产品口径。

### Full-Stack Software Engineer

- 改动 `mobile/web` cloud readiness panel，消费 `command_duplicate_deduped`，展示中文安全文案：“重复云指令已去重；机器人没有重复执行；这不是送达成功。”
- Start Delivery、Confirm Dropoff、Cancel 在 duplicate/deduped 状态下保持 disabled。
- 未新增自动 replay、自动 resubmit 或控制 endpoint；同步 fixture、mobile test 和 `docs/product/mobile_user_flow.md`。

### Product OKR Owner

- 本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 做 Product closeout。
- Objective 5 保守保持约 68%；Objective 1 保持约 81%；Objective 4 保持约 99%。

## 3. 验证结果

Engineer 已完成实现围栏：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 394 tests in 89.981s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
Ran 151 tests ... OK
```

```text
python3 -m py_compile remote_bridge.py operator_gateway_http.py operator_gateway_diagnostics.py: passed
node --check mobile/web/app.js: passed
required rg checks: passed
scoped git diff --check: passed
```

Product closeout 已复跑：

```bash
rg -n "cloud_command_idempotency_visibility_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_command_idempotency_visibility_guard|delivery success|真实公网 HTTPS/TLS|4G/SIM|production DB/queue" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard
git diff --check -- docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/fixtures/robot_diagnostics_cloud_command_idempotency_visibility_guard.json mobile/web/test_mobile_web_entrypoint.py
```

结果：

```text
required rg: matched expected closeout strings across OKR.md, docs/process/okr_progress_log.md, and sprint docs
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/...: passed with no output
git diff --check -- docs/product/... Robot/mobile implementation files: passed with no output
```

## 4. 偏差和修复

- Robot 首轮曾因 stale/pending priority 与 `ack_semantics` 检查失败；Robot worker 已定位并修复，重跑 focused suite 后通过。
- Product closeout 未改 Robot/mobile 代码，避免覆盖 Engineer 已完成实现。

## 5. 剩余风险

- 本轮不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER/UART/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。
- Objective 1 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`；真实 2D LiDAR / ToF 与 HIL materials 仍缺。
- ACK 只表示 command envelope / cached terminal ACK 处理，不代表真实送达成功。
