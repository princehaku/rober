# Sprint 2026.05.13_20-21 Mobile Primary Journey Gate - PRD

## 用户价值和产品北极星

用户价值：普通用户打开手机入口后，首先看到的是“我要去哪里、我是否已放好垃圾、现在能不能安全发车”的三步主路径，而不是多个 proof 面板和工程诊断堆叠。用户仍能看到阻塞原因、恢复建议、诊断/支持入口，但主操作逻辑要按普通用户理解方式组织。

产品北极星：`rober` 是一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。手机端必须让用户不接触 SSH、ROS2、串口、硬件调试或云端内部状态，也能完成或理解“确认目标 -> 确认放入垃圾 -> 安全发车/等待恢复”的核心任务路径。

## OKR 映射

- Objective 4 KR1：推进手机端最小流程，把连接/确认垃圾站/确认放入垃圾/一键发车/状态查看/异常处理收敛成首屏三步主路径。
- Objective 4 KR5：普通用户不接触命令行、不理解 ROS2，也能知道当前是否能继续，以及不能继续的原因。
- Objective 4 KR7：主操作主路径不超过三步，中文优先，首屏可理解，按钮态和 gate 语义清晰；本轮只做 Docker/local software proof。
- Objective 5：本轮只复用已有云中转、browser/device/cloud readiness 的 phone-safe metadata 作为阻塞/支持信息，不推进 O5 completion。

## KR 拆解或更新

本规划阶段不修改 `OKR.md`，只定义实现后 closeout 的 KR 判定口径：

- KR4.1-a：`mobile/web/` 首屏展示三步主路径 summary：目标垃圾站、已放入垃圾确认、发车安全 gate。
- KR4.1-b：三步主路径只消费已有 phone-safe 字段，不发明 robot state，不暴露 raw ROS topic、`/cmd_vel`、串口、波特率、WAVE ROVER 参数、凭证、local path、完整 artifact 或 checksum。
- KR4.1-c：Start 仍 fail closed；只有安全 gate、legacy `can_collect`、safe destination、用户已确认放入垃圾同时满足时才允许提交。
- KR4.1-d：ACK、HTTP accepted、action receipt 都只能表达 accepted/processing evidence，不表达送达成功、投放成功、取消完成或真实任务完成。
- KR4.1-e：Robot compatibility fence 证明 `mobile_primary_journey_gate` / `mobile_primary_journey_summary` metadata-only responses 不触发 collect、confirm_dropoff、cancel、不 POST ACK、不推进或持久化 cursor。

## 本轮核心抓手

核心抓手是 `software_proof_docker_mobile_primary_journey_gate`：

- 从“proof 面板堆叠”转为“普通用户三步主路径”。
- 保留已有 phone-safe readiness、command safety、device/browser/cloud gates、operation log、action feedback 作为主路径的证据和阻塞解释。
- 不扩大测试矩阵，只做 mobile entrypoint targeted unittest、robot metadata fence、py_compile 和 scoped diff check。

## 需要做什么

### Task A：Full-stack mobile primary journey summary/gate

责任人：`full-stack-software-engineer`

需要交付：

- 修改 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`，把首屏主路径组织为三步 summary：目标垃圾站 -> 已放入垃圾确认 -> 发车安全 gate。
- 使用现有 `phone_task_flow_readiness`、`command_safety`、`phone_readiness`、browser/device/cloud gates、operation log、action feedback 生成用户可读状态和阻塞原因。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`，提供 `mobile_primary_journey_gate` / `mobile_primary_journey_summary` 的 phone-safe fixture 示例。
- 更新 `mobile/test_mobile_web_entrypoint.py`，围栏验证三步主路径可渲染、Start fail closed、ACK 不是送达成功、危险字段不泄漏。
- 更新 `mobile/README.md` 和 `docs/product/mobile_user_flow.md`，写清本 gate 的用户价值、字段来源、非能力和证据边界。

### Task B：Robot metadata-only compatibility fence

责任人：`robot-software-engineer`

需要交付：

- 只做 metadata-only compatibility fence 与接口文档。
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`，加入 `mobile_primary_journey_gate` / `mobile_primary_journey_summary` metadata-only response 样本。
- 证明 metadata-only response 不触发 collect、confirm_dropoff、cancel，不 POST ACK，不推进 in-memory `last_ack_id`，不持久化 terminal cursor。
- 验证 valid collect command mixed metadata 仍只按 command envelope 执行动作，metadata 不改变 ACK/cursor 语义。
- 更新 `docs/interfaces/ros_contracts.md`，明确 primary journey metadata 是手机/支持 summary，不是 robot command、ACK、cursor、delivery success 或 HIL。

### Task C：Product closeout

责任人：`product-okr-owner`

需要在 A/B 返回后执行：

- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- 若 A/B 证据成立，建议只围绕 Objective 4 进行谨慎上调或说明保持；Objective 5 只有拿到真实外部材料才允许上调。
- closeout 必须写明 `software_proof_docker_mobile_primary_journey_gate` 不是真实手机设备、production app、真实 PWA install prompt、真实公网/4G/OSS/CDN/DB queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 优先级和验收口径

优先级：

1. P0：首屏三步主路径可被普通用户理解，且不掩盖 fail-closed 的安全 gate。
2. P0：Start/Confirm/Cancel 不因 summary 或 metadata 被误开；ACK 不被误写成成功。
3. P0：Robot metadata-only compatibility fence 通过。
4. P1：`docs/product/mobile_user_flow.md` 和 `mobile/README.md` 同步，避免文档滞后。

验收口径：

- 通过 targeted mobile unittest、robot metadata-only targeted unittest、py_compile 和 scoped `git diff --check`。
- 不要求 broad regression、不要求真实手机、不要求真实硬件、不要求真实公网。
- 所有输出必须保留 `software_proof_docker_mobile_primary_journey_gate` 和 `not_proven` 边界。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，用户触点、移动端主路径和产品流程文档。
- `robot-software-engineer`：Task B，remote bridge metadata compatibility fence 和接口文档。
- `product-okr-owner`：Task C，A/B 后的 sprint closeout、OKR 和进度日志。

## 风险、阻塞和需要补齐的证据链

- 当前没有真实 iPhone/Android device behavior，不能证明真实手机体验。
- 当前没有 production app 或真实 PWA install prompt，不能证明正式手机端安装体验。
- 当前没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue，Objective 5 不应因本轮上调。
- 当前没有 Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实投放或真实送达，本轮不碰 Objective 1/2/3 实机缺口。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。

## 需要创建或更新的 sprint 文档

本阶段已创建：

- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/pre_start.md`
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/prd.md`
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/tech-plan.md`

A/B 完成后必须继续创建或更新：

- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/tech-done.md`
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/side2side_check.md`
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/final.md`
