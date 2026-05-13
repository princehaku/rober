# Sprint 2026.05.13_23-24 Mobile Device Evidence Capture Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-13 23:02 Asia/Shanghai
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 统一证据边界：`software_proof_docker_mobile_device_evidence_capture_gate`
- 上一轮 sprint：`sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/`
- 上一轮提交：`8ae08ce Add mobile terminal action confirmation gate`

## 背景证据

`OKR.md` 4.1 当前数字最低的是 Objective 5，约 68%。但 `OKR.md` 第 6 节和上一轮 `final.md` 都写明：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 等真实外部材料时，不应继续推进 O5 completion，也不要重复堆本地 O5 metadata depth。

本机当前只有 Docker/local 软件验证环境，没有真实 WAVE ROVER/HIL、真实串口、真实手机设备/browser、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue。所以下一轮不继续消费 O5 外部材料 blocker，改推进 Objective 4 中仍可执行的手机端证据采集抓手。

上一轮 Objective 4 已完成 `software_proof_docker_mobile_terminal_action_confirmation_gate`：Confirm Dropoff / Cancel 首次点击只打开终端动作二次确认 panel，显式确认后才提交 compatible `trashbot.mobile_action_confirmation.v1` payload；Robot compatibility fence 证明 metadata-only summary 不触发 action、ACK 或 cursor。

## 本轮目标

建立 `mobile_device_evidence_capture`：让 `mobile/web/` 在真实浏览器环境中可以采集、展示并复制 phone-safe 的 device/browser/PWA 验收证据包，包括 viewport、touch target、display-mode/PWA、service worker/offline shell、client timestamp、evidence boundary、`not_proven` 和 ACK 语义。

本轮在 Docker/local 下只形成 `software_proof_docker_mobile_device_evidence_capture_gate`。即使实现了浏览器端采集逻辑，也不声明真实 iPhone/Android device behavior、production app、真实 PWA install prompt 或生产链路验收通过。

## Owner 与并行要求

Task A Full-stack 与 Task B Robot compatibility fence 文件范围互不重叠，后续必须并行启动：

- Task A Full-stack：负责 `mobile/web/` 采集/展示/复制证据包、fixture、targeted mobile unittest 和手机流程文档。
- Task B Robot compatibility fence：负责 remote bridge/protocol metadata-only 围栏和 ROS contract 文档，生产 `remote_bridge` 代码默认禁止改。
- Task C Product closeout：等待 A/B 返回后再更新 `OKR.md`、`docs/process/okr_progress_log.md` 与本 sprint 收口文档。

## 范围边界

本 sprint 不改硬件配置、launch 参数、Nav2/fixed-route、WAVE ROVER、UART、底盘协议或生产云配置。若 Task B targeted tests 证明 production remote_bridge 必须最小修复，必须先在返回中写明失败定位和最小修复理由，再由主会话决定是否扩大范围。

## 阻塞与风险

- Objective 5 外部材料仍缺失：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Objective 4 真实验收仍缺失：真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实手机设备/browser。
- 本轮只证明 Docker/local browser evidence capture software proof 和 robot metadata-only fence，不证明 Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
