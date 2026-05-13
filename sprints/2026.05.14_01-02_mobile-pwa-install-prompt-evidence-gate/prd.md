# Sprint 2026.05.14_01-02 Mobile PWA Install Prompt Evidence Gate - PRD

## 产品目标

把 `mobile/web/` 的真实手机验收交接能力推进到 PWA install prompt evidence gate。页面需要捕获、展示并复制 PWA install prompt 状态与安装验收结果，同时把真实 PWA install prompt 未观察到的缺口明确保留为 `not_proven`。

本轮结果不追求放行动作，而是让真实设备验收前的 PWA 安装证据链可执行、可复制、可交接、可被 Robot compatibility fence 证明不污染机器人命令链路。

## 用户价值和产品北极星

产品北极星：普通手机用户是唯一入口，用户不接触命令行、不理解 ROS2、不插线调试，也能发起任务、看懂状态、知道失败时如何求助。

本轮用户价值：

- 测试人员能在手机/PWA 验收区域看到 install prompt 是否被捕获、是否已被用户接受/拒绝、是否只是在 Docker/local 中未证明。
- 测试人员能复制 phone-safe PWA install evidence package，交给支持人员判断缺的是真实设备、真实浏览器、production app、真实 PWA install prompt，还是云/Robot 证据。
- 支持人员收到 package 后能看到 ACK 语义、evidence boundary、`not_proven` 和恢复建议，而不是从 raw browser/robot output 里猜。
- 产品侧继续保持保守边界：install prompt evidence 不是 Start/Confirm/Cancel 放行依据，也不是真实送达成功依据。

## OKR 映射

- 主要映射：Objective 4 KR5、KR7。真实手机用户验收标准要求普通用户不接触命令行、不插线调试，也能理解失败状态；手机端 UI 要适配真实设备、PWA/install prompt、首屏可交互和移动端验收口径。
- 支撑映射：Objective 5。当前 Objective 5 约 68% 且最低，但在缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 时，不继续堆本地 O5 metadata。本轮 pivot 到 Objective 4 是执行最近两轮 final 的 stop rule。
- 非映射：本轮不提升 Objective 1/2/3，不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff、真实 cancel 或真实 delivery。

## KR 拆解或更新

本轮计划阶段不直接修改 `OKR.md`。后续实现可按以下 KR 拆解验收：

- KR-A：`mobile/web/` 提供 `mobile_pwa_install_prompt_evidence`，可展示 install prompt capture status、user outcome、display-mode/installability/offline shell 摘要、安装验收结果和 `not_proven`。
- KR-B：复制包 schema 为 phone-safe metadata，包含 `schema=trashbot.mobile_pwa_install_prompt_evidence.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_mobile_pwa_install_prompt_evidence_gate`、ACK 语义、安全文案和 recovery hint。
- KR-C：复制包不得包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、串口、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifact 或 raw robot response。
- KR-D：缺真实手机/browser、production app、真实 PWA install prompt 时，Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。
- KR-E：Robot compatibility fence 证明 install prompt evidence、summary、package 属于 metadata-only，不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success claim。
- KR-F：Product closeout 只在 A/B 证据返回后决定 Objective 4 是否谨慎上调；若没有真实外部 O5 材料，Objective 5 不上调。

## 本轮核心抓手

把“真实 PWA install prompt 仍未证明”从 final 里的风险项前移到 `mobile/web/` 首屏证据面板。这个面板要让测试人员回答四个问题：

1. 当前浏览器是否捕获到 install prompt 相关事件或 fallback 状态。
2. 用户是否完成、拒绝或尚未执行安装验收。
3. 复制包是否足够 phone-safe，可以交给支持人员。
4. 哪些能力仍是 `not_proven`，尤其是真实 PWA install prompt、production app、真实 iPhone/Android device behavior、真实云/4G 和真实 delivery。

## 范围内需求

1. 后续 Task A 在 `mobile/web/` 新增或升级 PWA install prompt evidence 面板。
2. 面板必须包含：
   - install prompt capture status；
   - install prompt user outcome；
   - installability/display-mode/offline shell 摘要；
   - production app readiness 和 safe-to-control 摘要；
   - phone-safe copy package；
   - `ack_semantics=accepted_processing_only_not_delivery_success`；
   - `evidence_boundary=software_proof_docker_mobile_pwa_install_prompt_evidence_gate`；
   - `not_proven`。
3. 面板可消费已有 `mobile_device_handoff_session`、`mobile_device_evidence_capture`、`mobile_browser_acceptance_bundle` 或 device acceptance readiness，但不得把这些 support metadata 写成真实 PWA install prompt 通过。
4. Start Delivery、Confirm Dropoff、Cancel 必须继续受既有 readiness、browser acceptance bundle、terminal action confirmation、operation log/action feedback 和 command safety 控制；install prompt evidence 不能新增放行条件。
5. 后续 Task B 必须证明 install prompt evidence metadata-only，不进入 command、ACK、cursor、delivery result 或 production readiness。
6. 后续 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 必须同步写清字段、metadata-only 边界和 `not_proven` 范围。

## 范围外

- 不证明真实 iPhone/Android device behavior。
- 不证明 production app。
- 不证明真实 PWA install prompt。
- 不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实底盘运动、真实 dropoff/cancel completion 或真实 delivery。
- 不新增账户、登录、native app、生产云配置、真实外部流量验证或硬件配置。
- 不修改 `OKR.md` 或 sprint closure 文档，直到 A/B 返回后 Product Task C 执行。

## 优先级和验收口径

P0：

- PWA install prompt evidence 必须能在 `mobile/web/` 首屏或当前手机验收区域直接看到。
- 复制包必须 phone-safe，并保留 ACK 不是 delivery success 的边界。
- 缺真实 PWA install prompt 时必须显示 `not_proven`，不得写成验收通过。
- Start/Confirm/Cancel 不得因 install prompt evidence 存在而启用。
- Robot compatibility fence 必须证明 metadata-only。

P1：

- 面板要能指导真实手机测试人员观察 install prompt、display-mode、offline shell、manifest/service worker、viewport/touch target 和 production app readiness。
- 相关 product/interface docs 同步更新。

Product 验收只接受 A/B targeted tests、`py_compile`、`node --check`、scoped `git diff --check` 以及 closeout 文档证据。不接受口头描述、happy path 截图、copied package 本身或 Docker/local fixture 作为真实设备/PWA install prompt 通过证明。

## 对应责任 Engineer

- Full-stack Task A：`full-stack-software-engineer`
- Robot Task B：`robot-software-engineer`
- Product Task C：`product-okr-owner`

## 风险、阻塞和证据链

- 真实手机、production app、真实 PWA install prompt 仍需后续人工或设备侧证据补齐。
- O5 真实外部材料仍缺失；本轮不得把 O4 install prompt evidence 解释为 O5 completion。
- 若 A/B 返回的测试只覆盖 fixture/local browser，则证据边界仍是 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`。
- 若 copied package 中出现凭证、raw ROS topic、串口/硬件参数、本地路径或完整 artifact，Product closeout 必须阻断。
- 若 Start/Confirm/Cancel 被 install prompt evidence 放行，必须视为 P0 回归并退回对应 Engineer 修复。

## 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/pre_start.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/prd.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-plan.md`

A/B 返回后由 Product Task C 更新：

- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-done.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/side2side_check.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验收口径

本 sprint 完成时，Product 只接受以下证据：

- Task A targeted mobile unittest、`py_compile`、`node --check`、scoped diff check 通过。
- Task B targeted remote bridge/protocol unittest、`py_compile`、scoped diff check 通过。
- Task C 核对 A/B 输出后，收口文档清楚区分 software proof、真实 PWA install prompt proof、真实手机设备 proof、O5 外部材料 proof 和 delivery success。
- 没有真实外部 O5 材料时，Objective 5 不上调。
