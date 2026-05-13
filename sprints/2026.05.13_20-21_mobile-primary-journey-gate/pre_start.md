# Sprint 2026.05.13_20-21 Mobile Primary Journey Gate - Pre Start

## Sprint 类型

- `sprint_type: epic`
- 启动时间：2026-05-13 20:21 Asia/Shanghai
- 主目标：Objective 4 建立手机用户体验与低成本量产边界
- 关联目标：Objective 5 云中转 + OSS/CDN 数据通路产品化
- 证据边界目标：`software_proof_docker_mobile_primary_journey_gate`

## 用户原始要求

用户要求：“开始下一轮迭代，用 team 继续完成 OKR，功能往前走，测试只围栏，优先推进 OKR 完成度低的部分，本机只有 Docker，最后提交并推送。”

本规划阶段只创建 Epic sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`。实现、测试、OKR 更新和最终 closeout 由后续对应子 agent 完成。

## 开工证据

- `OKR.md` 4.1 更新时间为 2026-05-13 20:00，最新 sprint 为 `2026.05.13_19-20_mobile-pwa-installability-gate`。
- 当前完成度：Objective 5 约 68%，Objective 4 约 72%，Objective 1 约 75%，Objective 2/3 约 77%。
- `OKR.md` 第 6 节明确写明：Objective 5 只有拿到至少一种真实外部材料时才应继续推进 completion，包括 OSS/CDN live traffic、HTTPS/TLS 公网入口、4G/SIM、production DB/queue connectivity 或 production worker/migration 证据。
- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/final.md` 记录：没有真实外部材料，Objective 5 不上调，下一步若无外部材料应转向 Objective 4。
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/final.md` 记录：cloud-hosted PWA 是 Docker/local software proof，不是真实公网、真实手机设备或 production app；若外部环境仍不可用，应转向 Objective 4。
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/final.md` 记录：Objective 4 已完成 PWA installability software proof 到约 72%，Objective 5 因没有真实外部材料保持约 68%，下一步继续避免重复本地 O5 metadata depth。
- `docs/product/mobile_user_flow.md` 已定义 `mobile/web/` 只能消费 phone-safe `phone_readiness`、`command_safety`、`phone_task_flow_readiness`、operation log、action feedback、device/browser/cloud gates；Start 必须 fail closed，ACK 只是 accepted/processing evidence，不是 delivery success。

## 本轮选择

本轮不继续 Objective 5 本地 metadata 深挖，转向 Objective 4 的普通用户主路径：把 `mobile/web/` 首屏从多个 proof 面板堆叠，推进成普通用户可理解的“三步主路径” summary/gate。

选择理由：

- Objective 5 虽然是当前最低完成度，但没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 材料，继续 O5 会重复最近三轮已经明确限制的本地 proof。
- Objective 4 仍缺真实 iPhone/Android device behavior、production app、真实 PWA install prompt；在 Docker-only 条件下，本轮能推进的是软件可证明的主路径可理解性和 fail-closed gate。
- 普通用户主路径应先回答三个问题：目标垃圾站是什么、用户是否已确认放入垃圾、当前是否允许安全发车。proof 面板、诊断包、云状态和安装性证据应该支撑这个主路径，而不是替代主路径。
- 本机只有 Docker，不能宣称真实手机、真实 PWA install prompt、真实云/4G、真实送达、WAVE ROVER、HIL 或 production app。

## 本轮核心抓手

建立 `software_proof_docker_mobile_primary_journey_gate`：

- `mobile/web/` 首屏新增或重排“三步主路径” summary：目标垃圾站 -> 已放入垃圾确认 -> 发车安全 gate。
- 只消费已有 phone-safe 字段：`phone_task_flow_readiness`、`phone_readiness`、`command_safety`、browser/device/cloud gates、operation log 和 action feedback。
- 不发明机器人状态，不新增真实机器人语义，不把 ACK 写成送达成功。
- Robot 侧补 metadata-only compatibility fence，证明 `mobile_primary_journey_gate` / `mobile_primary_journey_summary` 不触发 collect、confirm_dropoff、cancel，不 POST ACK，不推进或持久化 cursor。
- Product closeout 在实现验证后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## Owner 和并行方式

- Task A：`full-stack-software-engineer`，负责 `mobile/web/` 三步主路径 summary/gate、fixture、移动端入口测试和产品文档。
- Task B：`robot-software-engineer`，负责 metadata-only compatibility fence 和接口文档。
- Task C：`product-okr-owner`，负责 A/B 完成后的 sprint closeout、OKR 和进度日志更新。

Task A 与 Task B 文件范围互不重叠，必须并行启动。Task C 依赖 A/B 结果，不能抢先写 closeout。

## Blocker 扫描

最近三轮都把“没有真实外部 O5 材料”写成 Objective 5 不上调或下一步转 O4 的依据。为避免第三轮继续消费同一 blocker，本轮明确切换到 Objective 4 的 Docker-only 可推进软件证明。

本轮不触碰 WAVE ROVER、ESP32、Orange Pi、UART、硬件 launch 参数、Nav2/fixed-route、真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue 或真实送达。

## 预期非目标

- 不证明真实 iPhone/Android device behavior。
- 不证明 production app。
- 不证明真实 PWA install prompt。
- 不证明真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。
- 不把 ACK、HTTP accepted 或 action receipt 写成 delivery success。
