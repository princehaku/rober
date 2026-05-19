# Sprint 2026.05.20_02-03 Cloud Command Expiry Safety Guard - Tech Done

## 1. Sprint 类型和证据边界

- sprint_type: epic
- Sprint 主题：`cloud_command_expiry_safety_guard`
- 证据边界：`software_proof_docker_cloud_command_expiry_safety_guard`
- 本轮只证明 Docker/local unit/static fixture 下的过期云命令 fail-closed 状态；不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER/UART/HIL、dropoff/cancel completion 或 delivery success。

## 2. 实际改动

### Robot Platform Engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`：过期云命令不提交本地 behavior action，继续 ACK `ignored`，并把 ACK result / operator status 标准化为 `degradation_state=command_expired`、`remote_ready=false`、`expired_command_id`、`primary_actions_enabled=false`、中文 safe copy、`retry_hint=resubmit_command` 和 `proof_boundary=software_proof_docker_cloud_command_expiry_safety_guard`。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`：保留 robot status 中的 phone-safe 降级白名单字段；MockCloudStore、`build_phone_readiness`、`trashbot.command_safety.v1` 和 offline/resume summary 识别 `command_expired`，禁用 Start / Confirm Dropoff / Cancel，保留 Diagnostics。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py` 与 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`：新增/扩展过期命令 ignored ACK、mock cloud readiness、phone readiness、command safety 的 fail-closed 断言；追加 missing/null `expires_at` 回归，确保非过期命令仍保持 pending 语义。
- `docs/product/remote_4g_mvp.md`：新增 Command Expiry Safety Guard 合同，明确本轮只属于 local/Docker software proof。

### User Touchpoint Full-Stack Engineer

- `mobile/web/app.js`：在既有 cloud readiness 只读面板中消费 `degradation_state=command_expired`、`expired_command_id`、`remote_ready=false`、`primary_actions_enabled=false` 和 `proof_boundary=software_proof_docker_cloud_command_expiry_safety_guard`；展示中文 safe copy、`ignored_expired_command_not_delivery_success` ACK 语义和 fail-closed recovery hint。
- `mobile/web/fixtures/robot_diagnostics_cloud_command_expiry_safety_guard.json`：新增 phone-safe fixture，明确旧命令被 ignored，不缓存、不重放、不触发 Start Delivery / Confirm Dropoff / Cancel。
- `mobile/web/test_mobile_web_entrypoint.py`：新增 cloud command expiry 测试，覆盖 app 消费、fixture fail-closed 字段、文档同步和 unsafe 文案过滤。
- `docs/product/mobile_user_flow.md`：补充 command expiry 用户旅程、字段语义和 recommended handling。

### Product Manager / OKR Owner

- `OKR.md`：更新 4.1 当前快照和 6 节优先级，保持 Objective 5 约 68%，明确本轮只是 `command_expired` / expired command ignored ACK 的 software proof。
- `docs/process/okr_progress_log.md`：追加本 sprint 进度条目，保留 O5 外部材料缺口、Objective 1 PR #5 thread 状态和 delivery success 边界。
- 本文件、`side2side_check.md`、`final.md`：整理 Robot / Full-Stack 草稿为正式 closeout，并记录 scoped validation。

## 3. 验证结果

### Robot Platform Engineer

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`：第一次失败于既有 auth flow 期望 `status_stale`，定位为 readiness 优先级把新鲜 pending 命令提前覆盖了 stale status；修复为 expired command 优先、普通 pending 保持 `status_stale -> command_pending` 既有顺序后重跑通过，`Ran 170 tests in 88.933s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`：focused operator rerun 通过，`Ran 44 tests in 23.920s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`：通过。
- `rg -n "cloud_command_expiry_safety_guard|command_expired|expired_command_id|remote_ready=false|primary_actions_enabled=false|delivery success|production DB/queue|4G" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md`：命中新增 guard 常量、字段、测试断言和文档边界；历史 `delivery success` / `production DB/queue` / `4G` 命中均为否定边界。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md`：通过。

### User Touchpoint Full-Stack Engineer

- `PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 145 tests in 1.126s`，`OK`。
- `node --check mobile/web/app.js`：通过，无语法错误。
- `rg -n "cloud_command_expiry_safety_guard|command_expired|expired_command_id|remote_ready=false|primary_actions_enabled=false|software_proof_docker_cloud_command_expiry_safety_guard|delivery success" mobile/web docs/product/mobile_user_flow.md`：命中新增 fixture、`app.js` 常量/派生分支、测试断言和产品文档；同时继续命中历史 `delivery success` 否定边界文案。
- `git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_expiry_safety_guard.json docs/product/mobile_user_flow.md`：通过。

### Product Closeout

- `rg -n "sprint_type: epic|cloud_command_expiry_safety_guard|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_command_expiry_safety_guard|OKR 最低优先级核对|delivery success" sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard OKR.md docs/process/okr_progress_log.md`：复跑通过，命中 sprint type、OKR 最低优先级核对、Objective 5、PR #5 unresolved thread、proof boundary 和 delivery success 否定边界。
- `rg -n "cloud_command_expiry_safety_guard|command_expired|expired_command_id|remote_ready=false|primary_actions_enabled=false|software_proof_docker_cloud_command_expiry_safety_guard|delivery success" mobile/web docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py docs/product/remote_4g_mvp.md`：复跑通过，命中 Robot / mobile / product docs 的新增字段与 proof boundary。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard`：通过。

## 4. 偏差和修复

- Robot 首轮 combined unittest 暴露 readiness 优先级回归：普通 pending command 不应提前覆盖 stale status；已由 Robot worker 修复并重跑通过。
- Robot follow-up regression 补齐 missing/null `expires_at`，确保非过期命令保持 pending，不被误判为 expired。
- Full-Stack 未新增控制 endpoint，也未改变 Start / Confirm Dropoff / Cancel gating，只做只读展示和 fixture/test/doc 同步。

## 5. 剩余风险

- Objective 5 仍保持约 68%，真实 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover、真实手机/browser。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`；本轮不得关闭该 thread，也不得提高 Objective 1。
- 本轮不证明真实 route/elevator field pass、dropoff/cancel completion、Nav2/fixed-route、WAVE ROVER/UART/HIL 或 delivery success。
