# Sprint 2026.05.14_07-08 Mobile Real Device Retest Request Gate - Tech Done

## Sprint 类型

- sprint_type: epic
- 当前状态：Task A/B/C 已完成，进入 sprint closeout
- 目标证据边界：`software_proof_docker_mobile_real_device_retest_request_gate`

## 用户价值和产品北极星

Task A 已把 review execution 的 blocked reason、next evidence request、evidence readiness、operator/reviewer notes、redaction/source boundary 和 `not_proven`，转成下一次真实设备复测可执行的 retest request package。

产品北极星保持不变：手机是普通用户唯一入口。本轮若完成，也只能收口为 Docker/local mobile software proof + Robot metadata-only fence；不能宣称真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实云、真实 4G、OSS/CDN live traffic、WAVE ROVER、HIL 或真实 delivery。

## OKR 映射

- Objective 4 KR5/KR7：真实设备验收材料从 review execution 推进到 retest request，支持下一轮真实设备复测按 missing evidence、material readiness/status、owner/next action、blocked/rejection reason 和 `not_proven` 执行。
- Objective 4 进度从约 83% 谨慎上调到约 84%；证据边界是 `software_proof_docker_mobile_real_device_retest_request_gate`。
- Objective 5：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，保持约 68%。
- Objective 1/2/3：本轮无硬件、导航、任务状态机、WAVE ROVER、串口、HIL、Nav2/fixed-route 或真实送达材料，不调整。

## 实际改动

### Task A Full-stack

`full-stack-software-engineer` 已完成：

- `mobile/web/index.html`：新增首屏“真实设备复测请求”panel，展示 retest checklist、missing evidence、material readiness、owner/next action、blocked/rejection reason、redaction/source boundary、ACK 和 `not_proven`。
- `mobile/web/app.js`：新增 `mobile_real_device_retest_request*` 候选读取、从 `mobile_real_device_review_execution*` 派生 retest request、phone-safe copy package 白名单、敏感词过滤补充、Start/Confirm/Cancel fail-closed gate。
- `mobile/web/styles.css`：把 retest panel/grid 纳入既有首屏面板样式。
- `mobile/fixtures/mobile_web_status.fixture.json`：新增顶层和 `phone_readiness` 下的 `mobile_real_device_retest_request`、summary、package fixture。
- `mobile/test_mobile_web_entrypoint.py`：新增 retest request 可见、可复制、非控制授权和 fixture 边界断言；现有 mobile web smoke 从 27 tests 扩到 28 tests。
- `mobile/README.md`：同步 retest request gate 边界、消费字段、白名单和非真实验收声明。
- `docs/product/mobile_user_flow.md`：同步 retest request 用户流程、接口语义、copy 白名单、敏感字段过滤和 fail-closed 边界。
- `sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/tech-done.md`：仅回填 Task A 实际改动、验证和风险。

实现结果：

- 新增/派生 `mobile_real_device_retest_request`、`mobile_real_device_retest_request_summary`、`mobile_real_device_retest_request_package`。
- 从 `mobile_real_device_review_execution*` 派生 retest request。
- 首屏展示 retest checklist、missing evidence list、readiness/status、owner/next action、blocked reason、rejection reason、redaction/source boundary、ACK-not-delivery 和 `not_proven`。
- copy package whitelist/phone-safe；过滤 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact、raw robot response、raw intake JSON 和 robot/internal technical fields。
- 缺真实设备材料、production app、真实 PWA install prompt/user choice 或 Objective 5 外部材料时，Start/Confirm/Cancel 继续 fail closed。

### Task B Robot

`robot-software-engineer` 已完成：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/tech-done.md`

实际实现：

- 在 `test_remote_bridge_protocol.py` 新增 protocol fence：`validate_command` 对混入 `mobile_real_device_retest_request`、`mobile_real_device_retest_request_summary`、`mobile_real_device_retest_request_package` 的有效 command 只返回 `trashbot.remote.v1` command envelope，不把 retest request metadata、`trigger_robot_action`、`cursor_override`、terminal ACK、delivery/dropoff/cancel success、production readiness、HIL、敏感 URL、Authorization、串口或 `/cmd_vel` 放进 normalized command。
- 在 `test_remote_bridge_protocol.py` 新增 metadata-only response fence：云端只有 retest request metadata、没有 command envelope 时，`RemoteCloudClient.get_next_command()` 返回 `None`，不合成 command id 或 terminal ACK，不 POST ACK，robot status POST 不携带 retest metadata 或 delivery success。
- 在 `test_remote_bridge.py` 新增 worker metadata-only fence：云端只有 retest request metadata 时，`RemoteBridgeWorker.poll_once()` 返回 `False`，不调用 collect、confirm_dropoff、cancel，不 POST ACK，不推进 `last_ack_id`，不创建 cursor persistence，不写 terminal ACK、production readiness、HIL、dropoff success、cancel completed 或 delivery success，status 保持 `waiting_for_trash`。
- 在 `test_remote_bridge.py` 新增 valid command mixed metadata fence：有效 `cancel` command 混入 retest request metadata 时只执行 cancel envelope；ACK、status、cursor persistence 和 terminal result 不携带 retest request metadata、success/production/HIL 字段或敏感字段。
- 在 `docs/interfaces/ros_contracts.md` 增加 retest request metadata 契约，明确该 metadata 只服务 phone/support/product 的下一轮真实设备复测材料请求，不得写入 robot control semantics，不得驱动 command、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery/dropoff/cancel success。

### Task C Product

`product-okr-owner` 已完成：

- `OKR.md`：更新 4.1 当前快照，把 Objective 4 从约 83% 谨慎上调到约 84%，Objective 5 保持约 68%，Objective 1/2/3 不调整。
- `docs/process/okr_progress_log.md`：在顶部记录本轮从 review execution 到 retest request 的证据边界、验证结果和未证明项。
- `sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/tech-done.md`：补齐 Task C 的 OKR、验证、失败定位、剩余风险和文档同步。
- `sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/side2side_check.md`：新增验收对照，确认 O5 最低但不选的理由仍成立。
- `sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/final.md`：新增 sprint final，收口 OKR 变更、证据等级、未完成项和下一步方向。

验收判断：

- `software_proof_docker_mobile_real_device_retest_request_gate` 成立，因为 Task A 的 mobile software proof 和 Task B 的 Robot metadata-only fence 均通过，且失败项已修复并复验。
- retest request package 只表示下一轮真实设备复测材料请求，不是真实设备验收通过、真实手机、production app、真实 PWA prompt/user choice、O5 外部 proof、HIL 或 delivery success。
- Objective 5 当前仍是最低 Objective，但本机只有 Docker，没有真实公网/4G/OSS/CDN/production DB/queue/worker 外部材料；继续做 O5 metadata 会重复消费 blocker，因此本轮 O4 retest request closeout 合理。

## 验证结果

### Task A Full-stack

已通过以下围栏验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 28 tests in 0.029s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit code 0

node --check mobile/web/app.js
exit code 0

rg -n "software_proof_docker_mobile_real_device_retest_request_gate|mobile_real_device_retest_request|retest request|missing evidence|owner|next action|blocked reason|rejection reason|ACK|not_proven|PWA install prompt|production app" mobile docs/product/mobile_user_flow.md
exit code 0

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/tech-done.md
exit code 0
```

### Task B Robot

已通过以下围栏验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 149 tests in 76.425s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit code 0

rg metadata-only / delivery success / production readiness / HIL checks
exit code 0; 覆盖 `mobile_real_device_retest_request*`、`software_proof_docker_mobile_real_device_retest_request_gate`、metadata-only、delivery success、cursor、terminal ACK、production readiness、HIL 关键词。

git diff --check scoped to Task B files
exit code 0
```

### Task C Product

已通过以下 closeout 验收：

```text
test -f sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/tech-done.md && test -f sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/side2side_check.md && test -f sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/final.md
exit code 0

rg -n "software_proof_docker_mobile_real_device_retest_request_gate|mobile_real_device_retest_request|Objective 5|Objective 4|not_proven|metadata-only|delivery success|retest request" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate
exit code 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate
exit code 0
```

## 失败定位

Task A Full-stack：首次 `node --check mobile/web/app.js` 失败，根因是在 `terminalActionGateFromStatus` 中重复声明 `mobileRealDeviceRetestRequest`。已删除重复声明并复验通过。

Task A Full-stack：首次 unit run 失败，根因是新增断言要求 `Objective 5 外部材料` 明确出现在 runtime contract 中，而 `app.js` 只保留了 `objective5_external_materials` 字段名。已补中文注释保留该边界并复验通过。

Task B Robot：未发现验证失败。

Task C Product：未发现验证失败。验收时仅发现需要新增 `side2side_check.md` 和 `final.md`，已补齐后通过文件存在、关键词和 scoped diff check。

## 剩余风险

Task A/B/C 已确认的剩余风险：

- `software_proof_docker_mobile_real_device_retest_request_gate` 只证明 Docker/local mobile software proof + robot metadata-only fence。
- retest request package 是下一轮真实设备复测材料请求，不是验收通过。
- 未证明真实 iPhone/Android、真实手机浏览器行为、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、WAVE ROVER、串口、HIL、Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。
- Task A 未运行真实手机、真实 production app、真实 PWA install prompt/user choice 或 Objective 5 外部材料验证；本轮只是 mobile/web local software proof。
- Task B 未运行真实硬件、真实手机、真实 production app 或 Objective 5 外部证据验证；这些必须由后续真实设备/外部环境材料补齐。
- Task C 未新增真实外部证据；OKR 上调仅限 Objective 4 的复测请求材料成熟度，不改变 Objective 5、HIL 或 delivery 边界。

## 文档同步与工程质量监管

- Full-stack 已同步 `docs/product/mobile_user_flow.md` 与 `mobile/README.md`。
- Robot 已同步 `docs/interfaces/ros_contracts.md`，新增 retest request metadata-only robot compatibility fence。
- Product 已同步 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint `tech-done.md` / `side2side_check.md` / `final.md`。
- Product closeout 未修改 mobile/onboard 代码或测试；对 Task A/B 新增代码的工程质量监管基于其回填结果：新增技术注释使用中文，验证围栏通过，未发现需要 Product 侧追加代码改动的问题。
