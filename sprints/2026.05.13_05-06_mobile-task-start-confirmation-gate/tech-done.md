# Sprint 2026.05.13_05-06 Mobile Task Start Confirmation Gate - Tech Done

## Full-stack Worker Result

### 实际改动

- `mobile/web/index.html`：在主操作区前新增发车确认区，展示目标垃圾站、目的地确认状态、Start 阻塞原因和"垃圾已放入"显式确认控件。
- `mobile/web/styles.css`：补充发车确认区、目的地 gate badge、确认网格和 checkbox 的手机端样式。
- `mobile/web/app.js`：从 `phone_task_flow_readiness.destination_summary`、`steps.destination_confirmed`、`phone_readiness.destination`、`status.destination` 提取 phone-safe destination；Start 继续受 `command_safety.actions.start.enabled=true` 与 `can_collect=true` 双 gate 约束，并新增 destination + loaded confirmation fail-closed；`/api/collect` 改为带 JSON body 的 phone-safe confirmation payload。
- `mobile/fixtures/mobile_web_status.fixture.json`：增加安全目的地摘要、destination confirmed step、load confirmation requirement 和 ACK 非送达成功语义。
- `mobile/test_mobile_web_entrypoint.py`：增加 Start 四重 gate、非 body-less collect POST、payload 安全字段、ACK 非 delivery success、缺 destination fail-closed 的静态契约检查。
- `docs/product/mobile_user_flow.md`：补充 Mobile Web Entrypoint 的发车确认 payload 与安全边界说明。
- 兼容性补充：`mobile/web/app.js` 的 Start payload 保留 `destination`，并新增同值 `target` 字段，避免旧 `/api/collect` 入口读取空目标；测试和产品流程文档已同步补充该契约。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint`
  - 结果：`Ran 6 tests in 0.001s`，`OK`。
- `git diff --check -- mobile/web/index.html mobile/web/styles.css mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-done.md`
  - 结果：通过，无输出。

### 剩余风险

- 本轮仍是 `software_proof_docker_mobile_task_start_confirmation_gate`，未证明真实手机设备/浏览器、production app、真实云/4G、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- "已放入垃圾"来自用户显式确认，不是自动载荷检测。
- ACK 仍只代表 accepted/processing，不代表 delivery success。

## Robot Worker Result

### Actual changes

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`: added a worker compatibility fence proving metadata-only cloud responses carrying `mobile_task_start_confirmation`, `mobile_task_start_confirmation_readiness`, and `task_start_confirmation_payload` do not start backend actions, post ACKs, advance in-memory cursor, or persist cursor state.
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`: added a protocol fence proving phone task-start confirmation metadata outside the `trashbot.remote.v1` command envelope is stripped from normalized robot commands.
- `docs/interfaces/ros_contracts.md` and `docs/product/remote_4g_mvp.md`: documented that phone confirmation payloads are UI/API confirmation records, not ROS2 action results, HIL, WAVE ROVER feedback, Nav2/fixed-route proof, ACK-as-delivery-success, or real delivery success.

### Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - Result: passed, `Ran 64 tests in 31.780s`, `OK`.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - Result: passed with no output.
- `git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md docs/product/remote_4g_mvp.md sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-done.md`
  - Result: passed with no output.

### Remaining risks

- This is a targeted software compatibility fence only. It does not prove real mobile device/browser behavior, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or real delivery success.
- No runtime parser changes were needed because the existing protocol helper already normalizes only `id`, `type`, `payload`, and `expires_at`.

## Product Closeout

### 阶段验收

- Product Owner 验收通过；阶段证据边界为 `software_proof_docker_mobile_task_start_confirmation_gate`。
- Objective 4 可从约 56% 保守上调到约 58%；Objective 1/2/3/5 不调整。
- 本轮证明手机本地入口的发车确认软件合同和 robot compatibility fence，不证明真实手机设备/浏览器、production app、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

### 收口文档

- 已补齐 `side2side_check.md`。
- 已补齐 `final.md`。
- 已更新 `OKR.md` 4.1。
- 已追加 `docs/process/okr_progress_log.md`。
