# Sprint 2026.05.12_18-19 Phone PWA Installability Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 18:19 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 主 OKR：Objective 5 - 手机体验与低成本量产边界
- 次支撑：Objective 6 - 远程/云状态摘要作为手机入口素材，本轮不做真实云
- 本轮证据目标：`software_proof_docker_phone_pwa_installability_gate`

## 上轮输入

`sprints/2026.05.12_17-18_remote-provisioning-audit-gate/final.md` 已把 O6 provisioning / STS / audit 的 Docker/local gate 收口到 `software_proof_docker_provisioning_audit_gate`，但仍明确缺真实云、真实 4G/SIM、真实 STS、真实 OSS upload、production-ready 和正式手机 app/真实设备验收。

O5 最近两轮已有可复用基础：

- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/final.md`：按钮级 command gate 已覆盖 Start、Confirm dropoff、Cancel、Diagnostics，并明确 ACK 只代表 command accepted/processing evidence，不等于送达成功。
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/final.md`：本地 Chrome 在 `390x844` 与 `768x900` viewport 通过 44px hit area、无重叠/无溢出、首屏主按钮可见、ACK copy 可见、Diagnostics 可访问、primary actions disabled。
- `docs/product/mobile_user_flow.md` 仍明确本地页面是 fallback 调试入口，不是 polished native app、account system 或真实手机设备验收。

## 用户价值和产品北极星

用户价值：普通手机用户进入本地 fallback 页面时，不只是在浏览器里临时打开一个 HTML，而是能获得接近生产手机入口的安装、离线壳层和阻断提示体验；网络或机器人状态不可用时，用户仍能看到 phone-safe 的离线壳层和下一步解释，而不是 raw JSON、ROS topic 或硬件细节。

产品北极星：手机是普通用户唯一入口。本轮不把 fallback 页面包装成正式 app，而是把它从“本地浏览器可用”推进到“PWA/installability 可证明”，为后续真实 iPhone/Android、账号系统和 4G 云入口验收打基础。

## OKR 映射

- O5 KR1：最小手机流程继续沿用连接入口、确认垃圾站、确认装载、一键发车、状态查看和异常处理，但本轮新增 PWA 安装入口边界。
- O5 KR5：用户不接触命令行、SSH、ROS2、串口或 raw JSON；离线壳层和 blocked state 必须解释为什么不能发车。
- O5 KR7：在已有 hit area/browser acceptance 基础上，补齐 `manifest`、mobile meta、service worker shell route 和 installability gate。
- O6 KR6：复用远程 readiness、manifest/provisioning/network/credential 等 phone-safe 摘要作为手机入口素材；本轮不证明真实云、4G、TLS、STS 或 OSS/CDN 实流量。

## 当前完成度判断

`OKR.md` 当前 2026-05-12 快照显示：

- O5：约 43%，证据边界是 `software_proof_docker_phone_browser_acceptance_gate`，仍缺生产手机 app、真实手机设备 Safari/Chrome、普通用户实机验收、生产账号或真实远程手机流程。
- O6：约 45%，证据边界是 `software_proof_docker_provisioning_audit_gate`，真实云、真实 4G/SIM、真实 STS、真实 OSS/CDN 和 production-ready 仍 blocked。

本机只有 Docker 且没有真实手机设备、真实云账号或硬件/HIL。按“优先推进 OKR 完成度低且当前可行动”的规则，本轮选择 O5，而不是继续堆 O6 真实云前置项或回到 O1/HIL。

## 本轮核心抓手

把本地 operator fallback 手机页面推进到 PWA/installability software proof：

- 提供 web manifest，包含 app name、short name、start URL、display mode、theme/background color、icons 和 phone-safe scope。
- 补齐 mobile meta，包括 viewport、theme color、apple mobile web app 相关 meta 和安全的标题/描述。
- 增加 service worker shell route，只缓存静态 shell 资源，不缓存 `/api/*` 动态状态、diagnostics、commands 或 ACK。
- 离线时页面只能展示 shell 与恢复提示，不能让 Start/Confirm/Cancel 进入可执行状态。
- API shape 和 command gate 兼容既有 tests，不因 PWA 壳层改变 `/api/status`、`/api/diagnostics`、`POST /api/collect`、`POST /api/dropoff/confirm`、`POST /api/cancel`。

## 需要做什么

1. `full-stack-software-engineer` 实现 PWA/installability gate：manifest、mobile meta、service worker shell route、offline shell copy、static serving 和 focused browser/HTTP helper。
2. `full-stack-software-engineer` 同步 `docs/product/mobile_user_flow.md`，明确 PWA 仍是 Docker/local fallback software proof，不是正式 app、真实手机设备或生产账号系统。
3. `robot-software-engineer` 仅在 API 或 command/status/ack 兼容性受影响时做只读/围栏验证，确认 service worker 不缓存 `/api/*`、不改变 ACK 语义、不触发额外 robot action。
4. `product-okr-owner` 在实现完成后更新 `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md`，只在证据充分时保守调整 O5。

## 优先级和验收口径

P0：

- Manifest 可通过 HTTP 获取且字段完整，scope/start URL 不暴露 raw API。
- HTML head 包含 mobile/installability meta。
- Service worker 能注册 shell route，但明确 bypass `/api/*`、commands、diagnostics 和 ACK 动态状态。
- 离线 shell 只展示 phone-safe copy、recovery hint 和 Diagnostics/刷新类安全入口；主操作 disabled。
- 既有 operator gateway HTTP/static tests 通过。
- 若新增 browser acceptance helper，只运行该单个 helper/测试，不做广泛回归。

P1：

- 输出可复查 artifact，记录 manifest fields、service worker cache policy、offline shell status、API bypass status、evidence boundary。
- 将 O6 phone-safe 摘要作为状态素材呈现，但不新增真实云工作。

验收边界：

- 可以声明 `software_proof_docker_phone_pwa_installability_gate`。
- 不得声明正式 app、真实手机设备 Safari/Chrome、真实 iPhone/Android 安装、真实云、真实 4G/SIM、真实 STS、真实 OSS/CDN、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 风险、阻塞和证据链缺口

- 本机只有 Docker，不能做真实手机设备安装、Safari/Android Chrome install prompt 或普通用户实机验收。
- PWA service worker 若错误缓存 `/api/*`，会把过期状态、ACK 或 command gate 展示给用户；这是本轮最高风险，必须写入 tests。
- 离线 shell 容易被误解为机器人可控制，必须保持 primary actions disabled，并用 phone-safe copy 说明需要重新连接。
- O6 摘要只能作为手机入口素材；本轮不扩大到真实云、TLS、STS、OSS/CDN 或 production account。
- 硬件/HIL、Nav2/fixed-route 和真实垃圾送达没有新证据，不能提升 O1-O4。

## 需要创建或更新的 sprint 文档

- 已创建：`sprints/2026.05.12_18-19_phone-pwa-installability-gate/pre_start.md`
- 本轮规划创建：`sprints/2026.05.12_18-19_phone-pwa-installability-gate/prd.md`
- 本轮规划创建：`sprints/2026.05.12_18-19_phone-pwa-installability-gate/tech-plan.md`
- 实现完成后更新：`tech-done.md`
- 验收完成后更新：`side2side_check.md`
- 收口完成后更新：`final.md`

