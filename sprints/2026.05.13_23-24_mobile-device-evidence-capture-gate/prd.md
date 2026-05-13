# Sprint 2026.05.13_23-24 Mobile Device Evidence Capture Gate - PRD

## 产品目标

普通手机用户和支持人员需要知道：当前手机页面是否具备进入真实设备验收的最低证据，缺哪些证明，以及如何把这些证据安全复制给支持人员。本轮把已有 blocked-by-design mobile acceptance readiness 进一步推进为浏览器端可采集、可展示、可复制的 `mobile_device_evidence_capture` 证据包。

## 用户价值

- 用户可以在手机页面看到当前浏览器视口、触控目标、PWA/display-mode、service worker/offline shell 和客户端时间等验收证据，而不是只看到抽象的 blocked 文案。
- 支持人员可以收到 phone-safe 证据包，用于判断是设备/browser/PWA 条件不足、生产 app 不存在、还是后端/robot gate 阻塞。
- 产品不会把 Docker/local 软件 proof 说成真实手机、生产 app、PWA install prompt、云/4G 或机器人实跑证明。

## 范围内需求

1. `mobile/web/` 首屏新增或升级 `mobile_device_evidence_capture` 面板。
2. 面板必须采集或展示：
   - viewport 宽高与 device pixel ratio；
   - touch target / pointer coarse 能力或等价 phone-safe 摘要；
   - display-mode / PWA install prompt readiness；
   - service worker/offline shell readiness；
   - client timestamp；
   - evidence boundary；
   - `not_proven`；
   - ACK accepted/processing-only 语义。
3. 面板必须提供复制 phone-safe evidence package 的入口，复制内容不得包含 token、Authorization、OSS AK/SK、root 密码、DB/queue URL、raw ROS topic、`/cmd_vel`、串口设备、波特率、WAVE ROVER 参数、本地路径、traceback、checksum 或完整 artifact。
4. 证据对象使用统一边界 `software_proof_docker_mobile_device_evidence_capture_gate`，可兼容已有 `mobile_device_acceptance_readiness` 与 `mobile_browser_acceptance_bundle`，但不能把 acceptance readiness 误写成真实验收通过。
5. Start Delivery、Confirm Dropoff、Cancel 的安全 gate 不能因本证据包存在而自动放开；真实手机/生产 app 缺失时仍 fail closed。
6. Robot side 必须证明 `mobile_device_evidence_capture` / summary / evidence package 属于 metadata-only，不得触发 command、ACK、cursor、delivery result 或 production readiness。

## 范围外

- 不证明真实 iPhone/Android device behavior。
- 不证明 production app。
- 不证明真实 PWA install prompt。
- 不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实底盘运动、真实 dropoff/cancel completion 或真实 delivery。
- 不新增账户、登录、production cloud 配置、native app 或云端外部流量验证。

## 验收口径

本轮完成时，Product 只接受以下证据：

- Task A targeted mobile unittest、`py_compile`、`node --check`、scoped diff check 通过。
- Task B targeted remote bridge/protocol unittest、`py_compile`、scoped diff check 通过。
- `docs/product/mobile_user_flow.md` 与 `docs/interfaces/ros_contracts.md` 同步写清 evidence capture 的 phone-safe 字段、metadata-only 边界和 not-proven 范围。
- `tech-done.md`、`side2side_check.md`、`final.md` 收口时不把 local/Docker proof 夸大为真实手机、生产 app、真实 PWA 或真实 delivery。

## OKR 对齐

本 sprint 面向 Objective 4。原因是 Objective 5 虽然数字最低，但当前没有真实外部 O5 材料可提升 completion；继续写本地 O5 metadata depth 会重复消费同一 blocker。Objective 4 的真实移动设备验收仍是当前用户体验最大缺口，本轮先把可采集证据包做成可验证的软件护栏。
