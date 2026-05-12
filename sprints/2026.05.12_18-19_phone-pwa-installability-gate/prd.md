# Sprint 2026.05.12_18-19 Phone PWA Installability Gate - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 18:19 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 evidence boundary：`software_proof_docker_phone_pwa_installability_gate`

## 用户价值和产品北极星

用户价值：普通手机用户需要一个“像手机入口”的控制面，而不是只能临时打开开发调试页。本轮让本地 fallback 页面具备 PWA 安装与离线壳层的最小产品边界：可被手机浏览器识别为可安装入口，断网或离线时不误导用户发车，并继续用普通话术解释恢复路径。

产品北极星：手机是普通用户唯一入口。本轮仍在 Docker/local software proof 内前进，不声明正式 app、真实设备验收或真实云闭环；它解决的是 O5 当前最低完成度里的“生产手机入口形态缺口”的一小步。

## 问题定义

现状已经有：

- 本地 operator fallback 页面。
- `/api/status.phone_readiness` 和 `command_safety`。
- 本地 Chrome viewport acceptance，证明 44px hit area、无重叠/无溢出、首屏主按钮可见和 blocked state 安全。

缺口是：

- 页面还没有 manifest、mobile installability meta 和 service worker shell route。
- 离线/断连时没有明确的 shell 行为和 phone-safe 文案边界。
- 仍不能把本地 fallback 页面与“正式 app/真实手机设备/生产账号系统”混淆。

## OKR 映射

主 OKR：Objective 5 - 手机体验与低成本量产边界。

- KR1：手机端最小流程保留，但入口从“能打开 local page”推进到“可被 PWA/installability gate 识别”。
- KR5：离线/阻断状态继续面向普通用户，不暴露命令行、SSH、ROS2、串口、raw JSON 或硬件细节。
- KR7：补齐安装性、移动端元信息、离线壳层和 PWA acceptance artifact。

次支撑：Objective 6 - 4G 云中转 + OSS/CDN 数据通路产品化。

- KR6：远程 readiness、manifest/provisioning/network/credential 等 phone-safe 摘要可作为手机入口素材。
- 本轮不做真实云、真实 4G/SIM、真实 TLS、真实 STS、真实 OSS upload 或 CDN origin fetch。

## KR 拆解或更新

本轮建议新增 O5 sprint-level KR：

- KR-PWA-1：`GET /manifest.webmanifest` 或等价 manifest route 返回完整 PWA manifest，且 scope/start URL 不直接指向 `/api/*`。
- KR-PWA-2：HTML head 包含 mobile viewport、theme color、apple mobile web app capable/title/status bar 等 meta，不破坏现有首屏布局。
- KR-PWA-3：Service worker 注册后只缓存静态 shell 资源；所有 `/api/*`、commands、diagnostics、ACK 和动态 status 请求必须 network-first 或 bypass cache。
- KR-PWA-4：离线 shell 显示 phone-safe copy 和 recovery hint，主操作按钮保持 disabled，不把离线 shell 当作机器人可控状态。
- KR-PWA-5：HTTP/static unit tests 与可选 browser/helper gate 产出 artifact，证明 installability、cache policy、offline shell 和 API bypass。

## 范围

In scope：

- Local operator fallback page PWA shell。
- Web manifest。
- Mobile/installability meta。
- Service worker registration and shell route。
- Offline shell copy and disabled primary actions。
- HTTP/static unit tests and focused helper if implementation needs it。
- `docs/product/mobile_user_flow.md` PWA boundary update。
- Sprint `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md` 在实现完成后的真实证据同步。

Out of scope：

- 正式 native app。
- 账号/login/paywall/production user system。
- 真实 iPhone/Android 设备验收。
- 真实云、公网 HTTPS/TLS、4G/SIM、真实 STS、真实 OSS/CDN。
- 新增机器人动作、底盘控制、Nav2/fixed-route、硬件/HIL。
- 缓存 `/api/*` 动态状态或让离线 shell 发出 command。

## 核心体验

1. 用户在手机浏览器打开本地 operator fallback 页面。
2. 浏览器能够识别 manifest 和 installability meta。
3. 页面注册 service worker 以支持 shell route。
4. 在线时，页面继续从 `/api/status`、`/api/diagnostics` 和 command endpoints 读取实时状态，遵守 command safety。
5. 离线或 API 不可达时，页面显示离线壳层、恢复提示和安全入口；Start/Confirm/Cancel 不可执行。
6. 用户看到的文案必须是 phone-safe，不出现 raw JSON、ROS topic、`/cmd_vel`、serial、baudrate、token、Authorization header、OSS secret 或硬件参数。

## 优先级和验收口径

P0 acceptance：

- Manifest route 可访问并返回 PWA 必需字段。
- HTML head mobile meta 可被测试定位。
- Service worker script 可访问并包含明确 API bypass 策略。
- Offline shell 或 offline fallback 文案存在，且 primary actions disabled。
- Existing HTTP/static tests pass。
- No API contract regression for `/api/status`、`/api/diagnostics`、`POST /api/collect`、`POST /api/dropoff/confirm`、`POST /api/cancel`。

P1 acceptance：

- Focused helper 输出 JSON artifact，字段至少包含 `manifest_status`、`mobile_meta_status`、`service_worker_status`、`api_cache_policy_status`、`offline_shell_status`、`evidence_boundary`。
- 若 helper 使用浏览器，只覆盖本轮 PWA/installability，不重复大范围 UI 回归。

## 对应责任 Engineer

- `full-stack-software-engineer`：主责实现、测试、文档同步和 PWA artifact。
- `robot-software-engineer`：若 API/cache/command compatibility 受影响，只做兼容性围栏验证；不新增 robot behavior。
- `product-okr-owner`：完成 sprint 收口、证据边界核对和 OKR 更新。

## 风险、阻塞和需要补齐的证据链

- 真实手机设备、真实 app install prompt 和普通用户实机验收仍 blocked；本轮只能是 Docker/local software proof。
- Service worker 缓存策略如果误缓存 API，会造成 status stale、ACK stale 或误启用主操作，必须用测试围住。
- 离线 shell 必须显式显示不可控制机器人，否则会给普通用户错误安全感。
- O6 素材只能作为状态摘要，不能让本轮变成真实云 sprint。
- O1/O2/O3/O4 没有新证据，不应更新完成度。

## 需要创建或更新的 sprint 文档

- 当前：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现后：`tech-done.md`
- 验收后：`side2side_check.md`
- 收口后：`final.md`

