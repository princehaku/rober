# Sprint 2026.05.13_22-23 Mobile Terminal Action Confirmation Gate - PRD

## 用户价值和产品北极星

用户在手机端点击 Confirm Dropoff 或 Cancel 时，正在做任务末端的高影响动作：一个动作可能被误解为“投放已完成”，另一个动作可能被误解为“机器人已经取消并安全停止”。在 Docker/local 证据边界内，产品不能证明真实投放完成、真实取消完成或真实 delivery success，因此手机 UI 必须先让用户看到动作、风险、ACK 语义和 not_proven，再要求用户显式确认。

本轮北极星是让普通手机用户能理解终端动作的真实含义：这是 accepted/processing 请求提交证据，不是 ROS2/机器人/云端/硬件完成证据。

## OKR 映射

- Objective 4 KR1：完善手机最小流程中的终端动作确认。
- Objective 4 KR5：用户无需理解 ROS2、remote bridge、ACK、cursor 或后台协议，也能知道动作是否只是提交请求。
- Objective 4 KR7：手机端 UI 更接近真实可用流程，但本轮仍是 Docker/local mobile software proof。
- Objective 5：不推进。当前缺少真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 和 production worker/migration 证据。

## KR 拆解或更新

本轮不新增 OKR 条目，只在 Objective 4 下补齐终端动作子能力：

- KR1 子能力：Confirm Dropoff / Cancel 必须从单击触发改为显式二次确认后触发。
- KR5 子能力：确认 panel 必须解释 ACK 是 accepted/processing only，不代表投放完成、取消完成或送达成功。
- KR7 子能力：确认 panel 必须适配手机首屏/主路径语义，保留取消/返回入口，避免用户误操作。

## 本轮核心抓手

`software_proof_docker_mobile_terminal_action_confirmation_gate`

该抓手包含两层：

1. `mobile/web/` 中 Confirm Dropoff / Cancel 点击后先进入只读确认 panel。
2. Robot 侧证明 `mobile_terminal_action_confirmation_gate` / summary 只是 metadata-only support summary，不触发 command、ACK、cursor 或 terminal cursor persistence。

## 需要做什么

### Task A：Full-stack mobile terminal action confirmation gate

责任 Engineer：`full-stack-software-engineer`

用户点击 Confirm Dropoff 或 Cancel 后，页面不得立即调用 endpoint。页面必须先展示确认 panel：

- action：`confirm_dropoff` 或 `cancel`。
- 风险：误确认可能导致用户误以为真实投放或取消已完成。
- ACK 语义：accepted/processing only，不是 delivery success、dropoff success 或 cancel completed。
- not_proven：真实 iPhone/Android、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实投放完成、真实取消完成、真实送达。
- `client_reference`：用户确认后提交 payload 时生成或展示。
- 取消/返回入口：用户可回到主路径，不发请求。
- 显式确认入口：用户确认后才调用现有 Confirm Dropoff / Cancel endpoint。

需要同步更新 fixture、targeted mobile test、`mobile/README.md` 和 `docs/product/mobile_user_flow.md`。

### Task B：Robot metadata-only fence

责任 Engineer：`robot-software-engineer`

为 `mobile_terminal_action_confirmation_gate` / summary metadata 增加 remote bridge/protocol fence：

- metadata-only response 不触发 collect。
- metadata-only response 不触发 confirm_dropoff。
- metadata-only response 不触发 cancel。
- metadata-only response 不 POST ACK。
- metadata-only response 不推进 `last_ack_id`。
- metadata-only response 不持久化 terminal cursor 或 cursor override。
- valid command envelope mixed metadata 仍只按 command envelope 执行。

需要同步更新接口文档，明确它是手机确认/支持 metadata，不是 robot command、ACK、cursor、delivery result、production readiness 或 HIL。

### Task C：Product closeout

责任 Engineer：`product-okr-owner`

A/B 完成后更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-done.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/side2side_check.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/final.md`

若 A/B 任一失败，Product 不直接收口为完成，必须要求对应 Engineer 定位并重试，或在 closeout 中明确失败定位和剩余风险。

## 优先级和验收口径

优先级：

1. P0：Confirm Dropoff / Cancel 必须先进入二次确认 panel，用户显式确认后才提交。
2. P0：ACK 和 evidence boundary 文案必须保守，不把 accepted/processing 当作完成。
3. P0：Robot metadata-only fence 必须证明 summary 不触发 command/ACK/cursor。
4. P1：Fixture、targeted tests 和 docs 同步。
5. P1：Product closeout 保守更新 OKR 和进度日志。

验收口径：

- `software_proof_docker_mobile_terminal_action_confirmation_gate` 出现在 fixture/docs/closeout。
- Confirm Dropoff / Cancel 的第一次点击不会调用 endpoint。
- 显式确认后才生成/提交 `trashbot.mobile_action_confirmation.v1` 兼容 payload。
- UI 显示 action、风险、ACK 语义、not_proven、client_reference、取消/返回入口。
- Robot 侧 metadata-only fence 对 collect/confirm_dropoff/cancel、ACK、cursor 均 fail closed。
- 所有验证只限 targeted unittest、`py_compile`、`node --check` 和 scoped `git diff --check`。

## 风险、阻塞和需要补齐的证据链

- 本机只有 Docker，无真实硬件、真实手机设备、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
- 该 gate 不证明真实投放完成、真实取消完成、真实 delivery success、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 如果实现中把 ACK、HTTP accepted、receipt 或 confirmation copy 写成成功完成，必须退回修正。
- 如果 robot fence 发现 metadata 会改变 ACK/cursor 或触发 action，必须由 `robot-software-engineer` 定位生产实现或测试契约问题后再收口。

## 需要创建或更新的 sprint 文档

已创建/本阶段更新：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

