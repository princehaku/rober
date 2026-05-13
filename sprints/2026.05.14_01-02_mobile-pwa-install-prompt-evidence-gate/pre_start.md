# Sprint 2026.05.14_01-02 Mobile PWA Install Prompt Evidence Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-14 01:02 Asia/Shanghai
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 统一证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_gate`
- 本轮功能名：`mobile-pwa-install-prompt-evidence`
- 上一轮 sprint：`sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/`
- 计划状态：只创建 `pre_start.md`、`prd.md`、`tech-plan.md`；不得创建 `tech-done.md`、`side2side_check.md` 或 `final.md`

## 背景证据

`OKR.md` 4.1 显示当前完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 4 当前约 77%。

最新 sprint `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/final.md` 明确：Objective 5 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料，不应继续堆本地 O5 metadata；可执行下一步是用 handoff session 采集真实手机、production app 或真实 PWA install prompt 证据。

前一轮 `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/final.md` 也给出相同 stop rule：若没有真实外部 O5 材料，优先推进 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt 或设备证据采集证明，不重复消费 O5 blocker。

当前用户明确本机没有真实硬件，只有 Docker。因此本轮只能建立 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`，不得写成 HIL、真实手机设备验收、真实 PWA install prompt、真实云证据、真实 4G/SIM、OSS/CDN live traffic 或 delivery success。

## 用户价值和产品北极星

产品北极星仍是让普通手机用户以手机作为唯一入口完成送垃圾主流程，并在失败或验收缺口出现时知道下一步该提供什么证据，而不是要求用户理解 ROS2、SSH、串口、云配置或 raw JSON。

本轮用户价值是把 PWA install prompt 这个真实设备验收缺口从口头提醒变成页面内可见、可复制、可交接的 evidence gate。测试人员在 Docker/local `mobile/web/` 中可以看到 install prompt 状态、安装验收结果、not_proven 缺口和安全复制包；支持人员可以据此判断下一步需要真实 iPhone/Android、production app、真实 PWA install prompt 还是云/Robot 证据。

## 本轮目标

建立 `mobile_pwa_install_prompt_evidence`：让 `mobile/web/` 能捕获、展示、复制 PWA install prompt 状态与安装验收结果，并让 robot compatibility fence 证明相关 metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK、cursor、delivery success 或 production readiness。

本轮必须保留以下边界：

- `software_proof_docker_mobile_pwa_install_prompt_evidence_gate` 只证明 Docker/local mobile software proof 和 robot metadata-only fence。
- `真实 PWA install prompt` 若未在真实设备/browser 中观察到，必须保持 `not_proven`。
- ACK、HTTP accepted、receipt、handoff session、evidence package 和 install prompt evidence 都只是 accepted/processing/support metadata，不是 delivery success。
- Start Delivery、Confirm Dropoff、Cancel 不得因为 install prompt evidence 存在而被放行。

## Owner 与并行要求

本 sprint 是 Epic，后续必须并行启动 A/B 两个 owner，C 等待 A/B 返回后收口：

- Task A Full-stack：负责 `mobile/web/` PWA install prompt evidence UI、fixture、targeted mobile unittest 和 `docs/product/mobile_user_flow.md` 更新。
- Task B Robot compatibility fence：负责 remote bridge/protocol metadata-only 围栏和 `docs/interfaces/ros_contracts.md` 更新，证明 install prompt evidence 不触发 robot action、ACK、cursor 或 delivery result。
- Task C Product closeout：等待 A/B 返回后再更新 `OKR.md`、`docs/process/okr_progress_log.md` 与本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。

## 范围边界

本轮只创建计划，不执行 A/B/C 实现，不修改 `OKR.md`、`docs/`、`mobile/web/`、Robot 测试或 closeout 文档。

后续实现不得改硬件配置、launch 参数、WAVE ROVER、UART、底盘协议、Nav2/fixed-route、production cloud 配置、真实凭证或外部云材料。PWA install prompt evidence 只能作为 phone/support metadata；不得作为 robot command、remote ACK、cursor instruction、delivery result、production readiness、HIL、真实手机设备验收或真实 PWA install prompt 通过证明。

## 阻塞与风险

- Objective 5 仍缺真实外部材料：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Objective 4 仍缺真实设备验收材料：真实 iPhone/Android device behavior、production app、真实 PWA install prompt。
- Docker/local 页面只能证明 install prompt evidence gate 的软件形态和复制边界，不证明浏览器真的触发了 beforeinstallprompt 或真实安装完成。
- 若后续 copied package 里出现 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、串口、WAVE ROVER 参数、本地路径、traceback、checksum 或完整 artifact，Product closeout 必须阻断。
