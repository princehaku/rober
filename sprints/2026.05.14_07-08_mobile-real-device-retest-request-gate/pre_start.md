# Sprint 2026.05.14_07-08 Mobile Real Device Retest Request Gate - Pre Start

## Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-14 07:00 Asia/Shanghai
- 目标证据边界：`software_proof_docker_mobile_real_device_retest_request_gate`
- 新 sprint folder：`sprints/2026.05.14_07-08_mobile-real-device-retest-request-gate/`

## 用户价值和产品北极星

用户价值是把上一轮真实设备 `review execution package` 中的 blocked reason、next evidence request、`not_proven` 和 source/redaction boundary，转成验收人员下一次可直接执行的 retest request package。验收人员不应再从 raw JSON、人工备注或多份 support package 里猜“下一轮真实设备复测缺什么”；手机/PWA 首屏需要直接展示复测 checklist、缺失材料、owner、next action、拒绝原因和证据边界。

产品北极星不变：普通用户只用手机完成低成本垃圾投递机器人任务，并且在证据不足时清楚知道下一步补什么。本轮仍是 Docker-only 软件证明，不是真实手机复测通过、production app 通过、真实 PWA install prompt/user choice、Objective 5 外部证据、HIL 或 delivery success。

## 开工证据

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%；Objective 4 当前约 83%。
- `OKR.md` 第 6 节明确：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 等真实外部材料时才继续推进 Objective 5 completion。无外部材料时不要重复本地 Objective 5 metadata depth，应转向 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 或主路径真实移动设备验收缺口。
- 最新 sprint `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/final.md` 已完成 `software_proof_docker_mobile_real_device_review_execution_gate`，但明确 review execution package 不是验收通过，仍缺真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实公网/4G/Objective 5 外部证据、HIL 和真实 delivery。
- 最新 final 的下一步要求：若继续没有 Objective 5 外部材料，应使用 review execution package 进入 Objective 4 的真实设备材料导入、真实 device behavior 记录、production app 或真实 PWA install prompt/user choice 实证。
- 用户本轮要求：开始下一轮 fresh epic sprint；建议下一步深入的 OKR 必须基于具体证据；用 team 继续完成 OKR；重新在功能往前走；测试只做围栏；优先推进完成度低的 OKR；本机没有真实硬件只有 Docker；后续实现完成后提交并推送。

## 本轮核心抓手

本轮抓手是 `mobile_real_device_retest_request*`：

- 从 `mobile_real_device_review_execution*` 派生 retest request。
- 把 blocked reason、next evidence request、not_proven、redaction/source boundary 转成复测人员下一轮需要补齐的材料清单。
- 首屏展示 retest checklist、missing evidence list、owner/next action、blocked reason、rejection reason、redaction/source boundary、ACK-not-delivery 和 `not_proven`。
- 复制包必须 whitelist/phone-safe，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact、raw robot response 或 robot/internal technical fields。
- Start / Confirm / Cancel 继续 fail closed；retest request package 不放行动作，不改变 command、status、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery success 语义。

## Scope 和 Owner

- Task A Full-stack：实现 `mobile_real_device_retest_request`、`mobile_real_device_retest_request_summary`、`mobile_real_device_retest_request_package`，更新手机/PWA、fixture、unit test、`mobile/README.md`、`docs/product/mobile_user_flow.md` 和本 sprint `tech-done.md`。
- Task B Robot：新增 `mobile_real_device_retest_request*` metadata-only / mixed valid-command fence，更新 remote bridge tests、protocol tests、`docs/interfaces/ros_contracts.md` 和本 sprint `tech-done.md`。
- Task C Product：等 A/B 完成后验收证据，更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。

Task A 与 Task B 文件范围互不重叠，必须并行启动 `full-stack-software-engineer` 与 `robot-software-engineer`。Task C 在 A/B 返回后执行验收和收口。Hardware 与 Autonomy 本轮无实现任务；如触及硬件或 Nav2/fixed-route 事实，只做只读补证，不扩大改动范围。

## 风险和阻塞

- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；本轮转 Objective 4 是避免第三次重复消费本地 Objective 5 metadata blocker。
- 真实 iPhone/Android、真实 device behavior、production app、真实 PWA install prompt/user choice 仍缺；retest request package 只能列出下一轮复测要补的材料，不能写成真实验收通过。
- 本轮没有 WAVE ROVER、Orange Pi UART、Nav2/fixed-route、真实 dropoff/cancel completion 或真实 delivery；Objective 1/2/3 不应因本轮上调。
- Robot 侧必须证明 retest request 是 metadata-only，不触发 command、status、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md` 待工程回填骨架

后续执行完成后由 Task C 创建或更新：

- `side2side_check.md`
- `final.md`
