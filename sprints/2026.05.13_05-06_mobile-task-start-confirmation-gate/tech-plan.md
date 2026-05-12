# Sprint 2026.05.13_05-06 Mobile Task Start Confirmation Gate - Tech Plan

## 目标

交付 `software_proof_docker_mobile_task_start_confirmation_gate`：让 `mobile/web/` 在 Start Delivery 前完成目标垃圾站确认和"已放入垃圾"确认，提交 phone-safe JSON payload 到 `POST /api/collect`，并保持 command_safety + 旧权限双 gate、离线/blocked fail-closed、ACK 仍只是 accepted/processing。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 4：手机用户体验与低成本量产边界，约 56%。
2. Objective 5 当前约 57%，上一轮 `2026.05.13_04-05_cloud-deployment-readiness-gate` 已完成 `software_proof_docker_cloud_deployment_readiness_gate`，但明确 Objective 4 未提升。
3. 本 sprint 直接针对 Objective 4。理由：03-04 已有 `mobile/web/` 静态入口，但还缺用户选择/确认垃圾站、确认已放入垃圾、带 body 的 collect payload 这条 KR1/KR5/KR7 主路径。

## 证据基线

- `OKR.md` 4.1：Objective 4 约 56%，缺口仍是 production app、真实手机浏览器/设备验收、真实 PWA install prompt、TTS/喇叭实放、量产实物验收。
- `03-04 final.md`：`software_proof_docker_mobile_web_entrypoint_gate` 只证明静态入口和 smoke 存在，不证明 production app、真实手机、云、4G、HIL 或真实送达。
- `03-04 tech-done.md`：`mobile/web/` 作为 dependency-free consumer，按钮启用由 `command_safety` 与旧权限共同决定。
- `04-05 final.md`：Objective 5 cloud deployment readiness 完成后 Objective 4 未调整。
- `04-05 tech-done.md`：cloud readiness 和 ACK 均保持非送达证明边界。
- `docs/product/mobile_user_flow.md`：Minimum User Journey 第 3-5 步要求确认垃圾站、放入垃圾、确认后开始；Start/Confirm/Cancel 默认禁用，只有 command safety 与旧权限都允许时启用；ACK 只代表 command processing。
- `mobile/web/app.js`：当前 `submitAction()` 对 `ENDPOINTS[actionName]` 只传 `{ method: "POST" }`，因此 collect 没有 phone-safe JSON body。

## 并行执行策略

本轮是 Epic sprint，跨 `full-stack-software-engineer` 与 `robot-software-engineer` 两个 owner，文件范围互不重叠，必须并行启动两个 worker。

### Worker A：full-stack-software-engineer

文件范围：

- `mobile/web/index.html`
- `mobile/web/styles.css`
- `mobile/web/app.js`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-done.md`

任务：

1. 在手机入口发车区展示或选择垃圾站，优先消费后端 phone-safe destination/task-flow 字段，缺字段时显示安全阻塞文案。
2. 增加"已放入垃圾"显式确认，未确认时 Start Delivery fail closed。
3. 修改 `POST /api/collect` 为 JSON body，包含 schema/version、source、destination、trash_loaded_confirmed、client reference/timestamp、ack semantics copy 或安全边界字段。
4. payload 不得包含 raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、credential、local path 或完整 artifact。
5. 保持 `command_safety.actions.start.enabled=true` 与旧权限 `can_collect=true` 双 gate；blocked/offline/pending ACK/manual takeover/缺字段/未确认时禁用。
6. 更新 mobile 静态 smoke 和 `docs/product/mobile_user_flow.md`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
git diff --check -- mobile/web/index.html mobile/web/styles.css mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-done.md
```

输出要求：

- 实际改动文件列表。
- 验证命令输出。
- 首轮失败定位和修复说明，如有。
- 剩余风险，尤其是真实手机/云/HIL/送达未证明。

### Worker B：robot-software-engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-done.md`

任务：

1. 增加 robot compatibility fence，证明 mobile task start confirmation payload 或相关 metadata 不触发非预期 robot backend call。
2. 证明 metadata-only 或 phone-confirmation 字段不 POST ACK、不推进内存 cursor、不持久化 cursor、不把 ACK 升级为 delivery success。
3. 证明合法 `trashbot.remote.v1` command envelope 仍只由既有 `id/type/payload` 语义决定，phone UI metadata 被剥离或忽略。
4. 更新接口文档，明确 phone confirmation payload 是 UI/API 层用户确认，不是 ROS2 action result、HIL、WAVE ROVER feedback 或 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md docs/product/remote_4g_mvp.md sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-done.md
```

输出要求：

- 实际改动文件列表。
- 验证命令输出。
- 首轮失败定位和修复说明，如有。
- 剩余风险，尤其是未证明 Nav2/fixed-route、HIL、WAVE ROVER 或真实送达。

## 接口影响

- `mobile/web/` 的 collect 请求从 body-less POST 升级为 JSON POST。
- 不改变 ROS2 action/service/topic contract。
- 不改变 `trashbot.remote.v1` command/status/ack envelope。
- 不改变 ACK 语义；ACK 仍是 accepted/processing evidence only。
- 后端若未支持新 payload，应 fail closed 或返回安全错误，不允许前端静默伪造成功。

## 产品验收口径

通过标准：

- `mobile/web/app.js` 不再对 `/api/collect` 发无 body POST。
- Start Delivery 前必须可见垃圾站确认和装载确认。
- 未确认垃圾站或未确认已放入垃圾时 Start Delivery 不可提交。
- `command_safety` + 旧权限双 gate 保持；缺任一 gate 都不放行。
- 离线、blocked、pending ACK、manual takeover 保持 fail closed。
- Diagnostics / Support Handoff 仍可用。
- ACK 文案明确不是送达成功。
- worker 验证命令通过，且 `tech-done.md` 记录实际改动、验证结果和剩余风险。

不通过标准：

- 仍存在 body-less collect POST。
- 只用 `window.confirm()` 代替持久可见的垃圾站/装载确认步骤。
- 只看 `can_collect` 或只看 `command_safety` 单 gate。
- 把 accepted/processing/ACK 写成 delivery success。
- payload 暴露 raw ROS/hardware/credential/local artifact 信息。

## 风险边界

- 本轮仍无真实手机设备、真实 production app、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。
- 本轮不证明自动载荷检测；"已放入垃圾"只是用户显式确认。
- 若后端 collect endpoint 暂不消费新 payload，本轮至少要证明前端发送 phone-safe body，并用测试保护字段安全与 fail-closed。

## Sprint 留档

计划阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现与收口阶段必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

最终 Product Owner 需要更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

本计划任务按用户限定文件范围，不修改上述收口文件。
