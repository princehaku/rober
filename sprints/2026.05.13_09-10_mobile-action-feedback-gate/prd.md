# Sprint 2026.05.13_09-10 Mobile Action Feedback Gate - PRD

## 背景

`OKR.md` 4.1 当前快照显示 Objective 4 手机用户体验与低成本量产边界约 60%，低于 Objective 5 约 61%，是当前最低且 Docker-only 可行动的 Objective。Objective 1/2/3 仍缺真实硬件、真实路线和 HIL 证据，本机只有 Docker，因此不能把本轮写成真实送达或真实上车验收。

最新 sprint `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/final.md` 只提升 Objective 5，不调整 Objective 4，并继续声明没有真实手机设备/browser、真实云/4G、HIL 或真实送达。最近提交 `cb29f53 Add mobile operation log gate` 已完成只读操作日志；`aa3490f Add cloud public ingress TLS gate` 继续强调 ACK 不是 delivery success、metadata-only 不触发机器人动作。

`mobile/README.md` roadmap 写明下一步是真实手机浏览器/设备验收、安装提示和弱网体验。但在当前 Docker-only 环境下，真实手机验收不可完成。本轮选择一个可验证且直接补用户体验缺口的 local/static gate：`mobile action feedback gate`。它让 Start/Confirm/Cancel 提交后在手机首屏显示 phone-safe 动作回执、失败提示和 ACK 语义，同时不把提交或 ACK 写成送达成功。

## 用户价值和产品北极星

用户价值：普通用户点击手机按钮后，必须立即知道这次动作请求处于什么状态：已提交、被拒绝、等待 ACK、失败、需要重试、需要人工接管，还是只能继续观察。用户不应看到 raw JSON、ROS topic、硬件参数或命令行式错误。

产品北极星：手机端是普通用户唯一入口。rober 的手机体验必须把"用户点击"、"命令被接收/处理中"、"机器人执行"、"任务完成"分成清晰证据层，避免 happy path 文案制造虚假闭环。

## 目标用户

- 普通手机用户：需要点击 Start/Confirm/Cancel 后看到明确反馈和下一步，不需要懂 ROS2、串口、云中转、ACK 或硬件。
- 家庭成员/操作员：需要在失败或等待时知道是否该重试、等待、取消、联系支持或人工接管。
- 售后/工程支持：需要可脱敏复现用户点击后的 phone-safe payload、client reference、失败原因和 ACK 语义。

## OKR 映射

- Objective 4 KR1：补齐手机端最小流程中一键发车、确认投放、取消后的动作反馈。
- Objective 4 KR4：动作回执和失败提示成为远程诊断最小数据包的一部分，帮助售后定位用户点击后发生了什么。
- Objective 4 KR5：用户不接触命令行、ROS2 或硬件调试，也能理解动作状态和异常处理。
- Objective 4 KR7：提升 phone-first 首屏可用性和中文优先文案；本轮仅为 local/static software proof。
- Objective 5 KR1/KR6：保护云中转 command/status/ack 语义，metadata-only action feedback 不得触发机器人动作或推进 cursor。

## KR 拆解或更新

### KR-A：手机动作回执面板

- `mobile/web/` 首屏新增或扩展动作反馈区域。
- Start/Confirm/Cancel 触发后展示 phone-safe 状态：submitted、accepted_or_processing、rejected、failed、blocked、waiting_ack 或等价枚举。
- 面板展示用户动作、client reference、safe phone copy、recovery hint、ACK 语义和 `not_proven` 边界。
- 文案必须中文优先，明确 ACK 是 accepted/processing evidence，不是 delivery success。

### KR-B：Generic mobile action confirmation payload

- Start 保留既有 `trashbot.mobile_task_start_confirmation.v1` 语义。
- Confirm Dropoff 和 Cancel 增加 generic mobile action confirmation payload，例如 `trashbot.mobile_action_confirmation.v1`。
- payload 字段只允许 phone-safe body：schema、schema_version、source、action、user_confirmed、client_reference、client_timestamp、safe_phone_copy、ack_semantics、evidence_boundary。
- payload 不包含 raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、credentials、本地路径、完整 artifact 或 checksum。

### KR-C：Fixture/static smoke 与文档同步

- `mobile/fixtures/mobile_web_status.fixture.json` 增加 action feedback / receipt 样例。
- `mobile/test_mobile_web_entrypoint.py` 覆盖动作反馈面板、ACK 文案、失败提示、Confirm/Cancel payload 生成或安全字段。
- `mobile/README.md` 和 `docs/product/mobile_user_flow.md` 写清 evidence boundary：`software_proof_docker_mobile_action_feedback_gate`。
- 文档明确本轮不证明真实手机设备/browser、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

### KR-D：Robot-side compatibility fence

- 增加 metadata-only 响应样例：`mobile_action_confirmation`、`mobile_action_receipt`、`phone_action_feedback` 或等价字段。
- 证明这些字段不触发 backend action。
- 证明不 POST ACK。
- 证明不推进或持久化 cursor。
- 证明 protocol normalization 剥离 command envelope 外 metadata。
- `docs/interfaces/ros_contracts.md` 写清 action feedback metadata 不改变 `trashbot.remote.v1` command/status/ack envelope。

### KR-E：Product closeout 与 OKR 口径

- 实现后由 product-okr-owner 更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`。
- Objective 4 可根据实际验证保守上调；Objective 1/2/3/5 除非有新证据不调整。
- final 必须保留非声明边界和剩余真实手机/真实云/真实硬件证据缺口。

## 本轮核心抓手

本轮抓手是"动作提交后的手机反馈闭环"。用户按下按钮后，系统要给出可理解、可恢复、可审计的反馈；同时工程上用 robot compatibility fence 保证这些反馈 metadata 不会被误消费为机器人动作或送达成功。

## 需要做什么

1. full-stack-software-engineer 实现 mobile/web 动作回执面板、Confirm/Cancel generic confirmation payload、fixture/static smoke 和手机流程文档更新。
2. robot-software-engineer 增加 robot-side compatibility fence，证明 mobile action feedback metadata-only 响应没有 backend side effect，并同步接口文档。
3. product-okr-owner 在实现完成后做 side-by-side 验收，更新 OKR、OKR progress log 和 sprint closeout。

## 优先级和验收口径

P0：

- Start/Confirm/Cancel 提交后有 phone-safe 动作回执或失败提示。
- Confirm/Cancel 请求带 generic mobile action confirmation payload，字段安全、可追溯、不含 raw/hardware/secret 信息。
- ACK copy 明确 accepted/processing only，不是 delivery success、dropoff success 或 cancel success。
- fixture/static smoke 覆盖动作回执、失败提示和 ACK 语义。
- Robot compatibility fence 证明 metadata-only action feedback 不触发 action、不 POST ACK、不推进或持久化 cursor。

P1：

- `mobile/README.md` 和 `docs/product/mobile_user_flow.md` 同步 action feedback contract、payload contract 和 evidence boundary。
- `docs/interfaces/ros_contracts.md` 同步 robot-side metadata-only contract。
- Product closeout 补齐 sprint 六文档链路并保守更新 Objective 4。

## 对应责任 Engineer

- full-stack-software-engineer：`mobile/web/`、mobile fixture/static smoke、`mobile/README.md`、`docs/product/mobile_user_flow.md`。
- robot-software-engineer：remote bridge/protocol compatibility tests、`docs/interfaces/ros_contracts.md`。
- product-okr-owner：`OKR.md`、`docs/process/okr_progress_log.md`、sprint `tech-done.md`、`side2side_check.md`、`final.md`。

## 非目标

- 不做真实手机设备/browser 验收。
- 不做真实 PWA install prompt、弱网实测或移动浏览器兼容矩阵。
- 不做真实云、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
- 不改 ROS2 runtime、Nav2/fixed-route、hardware launch、WAVE ROVER、UART 或 HIL。
- 不把提交成功、HTTP 200、ACK 或 receipt 写成 delivery success。
- 不新增大测试堆；只做 targeted unittest、`py_compile` 和 scoped diff check。

## 风险、阻塞和需要补齐的证据链

- 真实手机设备/browser 与弱网体验仍是后续 blocker；本轮只做 local/static software proof。
- 真实云/4G 与真实机器人执行缺失，动作 feedback 只能说明 phone/API 层收到或解释了请求，不能说明机器人完成动作。
- Confirm/Cancel payload 如果复用 Start 字段不当，可能产生语义混淆；实现必须用 action 枚举和 conservative ACK 文案区分。
- Robot metadata-only fence 若覆盖不足，后续 cloud relay 可能把 feedback 字段误当 command；Task B 必须用负例锁死。
- 本轮证据链：targeted mobile unittest、targeted remote bridge/protocol unittest、`py_compile`、scoped `git diff --check`，必要时 static fixture smoke。
