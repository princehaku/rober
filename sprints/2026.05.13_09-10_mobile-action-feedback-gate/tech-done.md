# Sprint 2026.05.13_09-10 Mobile Action Feedback Gate - Tech Done

## Task A Full-Stack Mobile Action Feedback Gate

### 实际改动

- `mobile/web/index.html`：首屏新增动作回执面板，展示最近一次 Start / Confirm Dropoff / Cancel 的动作、提交状态、失败或阻塞原因、恢复建议、`client_reference`、ACK 语义和 evidence boundary。
- `mobile/web/app.js`：增加 `mobile_action_receipt` / `phone_action_feedback` 消费与本地提交失败 copy；Start Delivery 保持既有 `trashbot.mobile_task_start_confirmation.v1` gate；Confirm Dropoff / Cancel 增加 `trashbot.mobile_action_confirmation.v1` phone-safe payload。
- `mobile/web/styles.css`：增加动作回执面板样式，保持手机首屏可读且不改变安全 gate。
- `mobile/test_mobile_web_entrypoint.py`：增加动作回执、失败提示、Confirm/Cancel payload、安全字段和 ACK 语义的 static smoke 围栏；初次失败定位为新增断言误把否定式 ACK 风险文案里的"投放完成/取消已落地"当成正向完成声明，已修正。
- `mobile/fixtures/mobile_web_status.fixture.json`：增加动作回执 fixture，继续标注为 static smoke fixture，不是真实机器人状态。
- `mobile/README.md`、`docs/product/mobile_user_flow.md`：同步动作回执规则、payload contract、证据边界和非声明边界。

### 用户旅程变化和触点收益

用户点击 Start / Confirm Dropoff / Cancel 后，首屏现在能说明"刚提交了什么、提交是否被接受或阻塞、下一步该等待还是重试、需要什么恢复动作"。这补齐了上轮只读 operation log 之后的主操作反馈缺口，但不会把 accepted/processing 证据包装成真实机器人执行结果。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
```

结果：`Ran 9 tests in 0.002s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
```

结果：通过，无输出。

```bash
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/README.md docs/product/mobile_user_flow.md
```

结果：通过，无输出。

### 剩余风险

- 本 Task A 只建立 local/static mobile action feedback software proof，不证明真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。
- Confirm/Cancel payload 是 phone-safe confirmation envelope，不是机器人动作完成证明。

## Task B Robot Compatibility Fence

### 实际改动

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`：新增 `mobile_action_confirmation` / `mobile_action_receipt` / `phone_action_feedback` metadata-only response 围栏，验证不触发 backend action、不 POST ACK、不推进内存 cursor、不创建 cursor state file。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`：新增 protocol normalization 围栏，确认 command envelope 外的 action-feedback metadata 会被剥离，不进入 robot command payload。
- `docs/interfaces/ros_contracts.md`：明确 action feedback metadata 是 phone-safe support/status summary，不属于 `trashbot.remote.v1` command/status/ACK envelope；ACK 仍只是 accepted/processing evidence，不是 delivery success。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：`Ran 74 tests in 37.525s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：通过，无输出。

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

结果：通过，无输出。

### 剩余风险

- 本 Task B 只证明 robot-side software compatibility fence，不证明真实云/4G、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- metadata-only action feedback 仍必须作为状态/支持摘要处理，不能进入 robot command path。

## Task C Product Closeout

### 用户价值和产品北极星

本轮用户价值是让普通手机用户在点击主操作后立即看到可解释、可恢复、可审计的动作反馈，而不是只看到按钮状态或猜测机器人是否执行。产品北极星保持不变：手机端必须成为普通用户完成送垃圾任务的唯一入口，并且把用户提交、ACK accepted/processing、机器人执行和真实送达成功分成清晰证据层。

### OKR 映射和 KR 拆解

- Objective 4 KR1：补齐手机最小流程中 Start、Confirm Dropoff、Cancel 提交后的动作反馈。
- Objective 4 KR4：把动作回执、失败原因、恢复建议和 client reference 纳入 phone-safe 诊断语义。
- Objective 4 KR5：普通用户无需命令行、ROS2 或硬件知识，也能知道动作是否被接受/阻塞以及下一步。
- Objective 4 KR7：提升手机首屏主路径可用性；本轮仍是 local/static software proof。
- Objective 5 KR1/KR6：通过 robot-side compatibility fence 保护 `trashbot.remote.v1` command/status/ACK envelope，避免 metadata-only feedback 触发机器人动作。

### 本轮核心抓手

- Task A 交付手机端动作回执面板和 Confirm/Cancel generic confirmation payload。
- Task B 交付 robot metadata-only compatibility fence。
- Task C 完成 sprint closeout、OKR 当前快照和 OKR 进度日志同步。

### 责任 Engineer 和验收口径

- Task A：`full-stack-software-engineer` 主责手机动作回执、payload、fixture/static smoke 和手机流程文档。
- Task B：`robot-software-engineer` 主责 remote bridge/protocol compatibility fence 和接口文档。
- Task C：`product-okr-owner` 主责验收、OKR 更新、进度日志和 sprint 收口。

验收口径：只接受 targeted unittest、`py_compile`、scoped diff check 和引用路径存在性检查；不把 ACK、HTTP accepted、receipt、metadata-only response 或 static fixture 解释成 delivery success、真实手机验收、真实云/4G、HIL 或真实送达。

### Task C 验证结果

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
```

结果：通过，exit 0，无输出。

```bash
test -f sprints/2026.05.13_09-10_mobile-action-feedback-gate/tech-done.md && test -f sprints/2026.05.13_09-10_mobile-action-feedback-gate/side2side_check.md && test -f sprints/2026.05.13_09-10_mobile-action-feedback-gate/final.md
```

结果：通过，exit 0，无输出。

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_09-10_mobile-action-feedback-gate
```

结果：通过，exit 0，无输出。

### 剩余风险

- 本 sprint 证据边界是 `software_proof_docker_mobile_action_feedback_gate`。
- 不声明真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
