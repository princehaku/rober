# Sprint 2026.05.20_01-02 Cloud Pending ACK Status Guard - Tech Done

## 1. Sprint 类型

- sprint_type: epic
- 收口时间：2026-05-20 01:41 Asia/Shanghai。
- 证据边界：`software_proof_docker_cloud_pending_ack_status_guard`。
- 本轮只证明 Docker/local unit/static fixture 下的 pending ACK status guard，不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。

## 2. 实际改动

### robot-software-engineer

- 修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`：
  - 新增 `software_proof_docker_cloud_pending_ack_status_guard` status boundary。
  - pending terminal ACK post/replay 失败时输出 `degradation_state=command_pending`、`remote_ready=false`、`pending_terminal_ack_id`、`primary_actions_enabled=false`、`safe_phone_copy`、`retry_hint` 和 proof boundary。
  - pending ACK 成功前不推进 `last_terminal_ack_id`，不 fetch new command，不重复本地 action。
  - 修复状态文件中显式空 `last_terminal_ack_id` 被 fallback 覆盖的 cursor recovery edge case。
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`：
  - 覆盖 pending ACK replay failure、status redaction、no cursor advance、no new command fetch、no duplicate action 和 explicit empty cursor recovery。
- 修改 `docs/product/remote_4g_mvp.md`：
  - 补充 pending ACK status guard 的触发条件、状态字段、fail-closed 行为和证据边界。

### full-stack-software-engineer

- 修改 `mobile/web/app.js`：
  - 既有 cloud readiness panel 消费 top-level/readiness `remote_readiness`、`remote_status` 和 `degradation_state=command_pending`。
  - 归一化 `remote_ready=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和中文 safe copy。
- 修改 `mobile/web/test_mobile_web_entrypoint.py`：
  - 覆盖 command pending copy、disabled actions、`remote_ready=false`、`primary_actions_enabled=false` 和 no delivery success claim。
- 新增 `mobile/web/fixtures/robot_diagnostics_cloud_pending_ack_status_guard.json`。
- 修改 `docs/product/mobile_user_flow.md`：
  - 记录手机端只读展示该 cloud pending ACK 降级状态，保持本地软件 proof 边界。

### product-okr-owner

- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 创建 `tech-done.md`、`side2side_check.md` 和 `final.md`，完成本轮 closeout。

## 3. 验证结果

Product closeout 复跑指定围栏：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 127 tests ... OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
exit 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
Ran 143 tests ... OK
```

```text
node --check mobile/web/app.js
exit 0
```

```text
rg -n "cloud_pending_ack_status_guard|command_pending|remote_ready=false|primary_actions_enabled=false|software_proof_docker_cloud_pending_ack_status_guard|Objective 5|PRRT_kwDOSWB9286CJ3tX|delivery success|production DB/queue|4G" ...
matched required implementation, docs, OKR, progress log, mobile fixture, tests and sprint closeout strings
```

```text
git diff --check -- <scoped files>
exit 0
git diff --cached --check
exit 0
```

## 4. 偏差和失败定位

- 未发现验证失败。
- 本轮没有真实外部云、真实 4G/SIM、真实 production DB/queue、真实 OSS/CDN live traffic、真实手机/browser、WAVE ROVER/UART/HIL 或 route/elevator field materials，因此 Objective 5、Objective 4、Objective 2、Objective 3 和 Objective 1 均不因本轮上调百分比。

## 5. 剩余风险

- O5 completion 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、多实例一致性、queue ordering、transaction isolation、backup/recovery 和真实手机/browser。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 本轮 `remote_ready=false` 与 `primary_actions_enabled=false` 是 pending ACK 降级状态的软件证明，不是 delivery success、HIL、真实手机验收或 production cutover。
