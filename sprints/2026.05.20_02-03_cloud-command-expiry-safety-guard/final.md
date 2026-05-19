# Sprint 2026.05.20_02-03 Cloud Command Expiry Safety Guard - Final

## 1. 收口结论

- sprint_type: epic
- 本轮完成 `cloud_command_expiry_safety_guard` 的 Docker/local software proof：过期云端 command 不提交本地 action，ACK `ignored`，Robot/operator/mobile 都能看到 `command_expired` 的 fail-closed 状态。
- 证据边界：`software_proof_docker_cloud_command_expiry_safety_guard`。
- Objective 5 保持约 68%；本轮不证明真实 O5 external proof，不提高 O5 completion。
- Objective 1 保持约 81%；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，不得由本轮关闭或抬升 O1。

## 2. 用户价值和产品北极星

本轮用户价值是防止普通手机用户在弱网、排队或机器人离线后误以为旧云命令仍会执行。系统现在明确表达“旧命令已过期且没有执行，请重新下发”，并保持主操作 fail-closed。这服务于北极星：普通手机用户能安全、可理解地使用云中转控制送垃圾机器人，而不是把 ACK、ignored 或 stale 状态误解为真实送达。

## 3. OKR 映射和 KR 结果

- Objective 5 KR1：command/status/ack 契约补齐 expired command ignored ACK 的状态可见性；本轮是 local/mock contract proof。
- Objective 5 KR6：过期 command 成为 graceful degradation 的明确状态，`retry_hint=resubmit_command`。
- Objective 4：手机端只读展示 `command_expired` 中文 safe copy，Start / Confirm Dropoff / Cancel 继续 disabled。
- KR 未完成部分：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 仍缺。

## 4. 本轮核心抓手

- Robot 把 expired command 从“只 ignored ACK”推进到可观测 readiness/status：`degradation_state=command_expired`、`remote_ready=false`、`expired_command_id`、`primary_actions_enabled=false`、safe copy、`retry_hint=resubmit_command` 和 proof boundary。
- Full-Stack 沿用既有 cloud readiness panel 消费该状态，不新增控制 endpoint、不缓存、不重放、不自动 resubmit 过期控制请求。
- Product closeout 保持证据边界，不把本轮写成 delivery success、真实手机/browser、真实云或生产外部材料 proof。

## 5. 责任 Engineer 和实际结果

- `robot-software-engineer`：完成 `remote_bridge.py`、`operator_gateway_http.py`、Robot tests 和 `docs/product/remote_4g_mvp.md`；首轮验证失败后定位 readiness 优先级并修复，最终 combined unittest `Ran 170 tests in 88.933s OK`，focused operator rerun `Ran 44 tests in 23.920s OK`。
- `full-stack-software-engineer`：完成 `mobile/web/app.js`、fixture、mobile tests 和 `docs/product/mobile_user_flow.md`；`mobile/web/test_mobile_web_entrypoint.py` `Ran 145 tests in 1.126s OK`，`node --check mobile/web/app.js` 通过。
- `product-okr-owner`：完成 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md` 和本 `final.md`；复跑 scoped closeout validation。

## 6. 验收结果

- Product required `rg` for sprint/OKR/progress log：通过，覆盖 `sprint_type: epic`、`cloud_command_expiry_safety_guard`、Objective 5、`PRRT_kwDOSWB9286CJ3tX`、proof boundary、OKR 最低优先级核对和 delivery success 否定边界。
- Product required `rg` for implementation/product docs：通过，覆盖 `command_expired`、`expired_command_id`、`remote_ready=false`、`primary_actions_enabled=false`、proof boundary 和 delivery success 否定边界。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard`：通过。

## 7. 风险、阻塞和证据缺口

- O5 仍 blocked on real external materials：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser。
- O1 / PR #5 仍 blocked on real materials：`PRRT_kwDOSWB9286CJ3tX` unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，以及真实 WAVE ROVER/UART/HIL。
- 本轮不证明真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、WAVE ROVER motion、HIL 或 delivery success。
- 下一轮若仍没有 O5/O1 真实材料，应避免重复本地 metadata depth，改按 live OKR rerank 选择能拿到真实材料或能消除具体软件风险的抓手。
