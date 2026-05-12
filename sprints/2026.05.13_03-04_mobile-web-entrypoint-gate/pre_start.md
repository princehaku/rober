# Sprint 2026.05.13_03-04 Mobile Web Entrypoint Gate - Pre Start

## Sprint Type

- sprint_type: epic
- Theme: `mobile-web-entrypoint-gate`
- Product Owner: `product-okr-owner`
- Primary Objective: Objective 4 - 手机用户体验与低成本量产边界
- Secondary Guardrail: Objective 5 - 云中转 + OSS/CDN 数据通路产品化 contract compatibility
- Evidence boundary target: `software_proof_docker_mobile_web_entrypoint_gate`
- OKR number update: 本启动任务不更新 `OKR.md` 数字；最终收口时再按验证证据保守评估。

## 用户价值和产品北极星

用户价值：普通手机用户应该打开一个明确的手机入口就能看到连接状态、任务主路径、异常解释、诊断/求助入口和离线恢复提示，而不是依赖 onboard fallback 大字符串、SSH、ROS2 topic 或 raw JSON。

产品北极星：把 rober 做成手机可操作的低成本 ROS2 送垃圾机器人。本轮只推进手机 PWA 入口的软件边界，不声明真实手机设备、真实云/4G、OSS/CDN 实流量、WAVE ROVER、HIL 或真实送达闭环。

## 启动证据

- `OKR.md` 4.1 当前快照显示 Objective 4 约 54%，Objective 5 约 55%，Objective 1/2/3 均约 75% 以上但本机没有真实硬件证据，真实 HIL/串口/Nav2/fixed-route 仍缺。
- `sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/final.md` 已闭合 `cloud-relay/` self-contained runtime gate，但明确留下正式手机 app、真实手机设备/浏览器、真实云、4G、OSS/CDN、HIL 和真实送达缺口。
- `sprints/2026.05.13_01-02_codebase-restructure-four-tier/final.md` 明确四分层目录已落地，但 P5 没有实施，`mobile/` 只是新部署单位。
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/final.md` 已有 offline/resume gate 和 robot compatibility fence，但证据仍是 local/Docker fallback。
- `mobile/README.md` 写明 `mobile/web/` 预期承接 PWA 前端静态资源，当前状态仍是 README 脚手架，`operator_gateway_static.py` 内嵌 HTML/CSS/JS 尚未抽出。
- `docs/process/okr_progress_log.md` 记录 00-01、01-02、02-03 的证据边界均没有真实手机设备/production app 验收。

## 上轮未完成项和本轮切换原因

02-03 建议继续 Objective 5 的真实云前置链路，但 live `OKR.md` 里 Objective 4 低于 Objective 5，且最近三轮已经证明云中转 self-contained runtime、目录脚手架和 phone offline/resume fallback 均没有解决正式手机入口缺口。因此本轮切换到 Objective 4，不重复消费 cloud-relay Docker/local gate。

本轮不触碰 WAVE ROVER、ESP32、Orange Pi、UART、电气、机械或 HIL 配置；无需读取 vendor 硬件资料作为实现前置。若后续 worker 任务新增任何硬件事实，必须回到 `docs/vendor/VENDOR_INDEX.md`。

## 本轮核心抓手

1. 在 `mobile/web/` 形成 dependency-free phone PWA entrypoint，使手机端有独立静态入口，而不是继续依赖 onboard fallback 大字符串。
2. 入口只消费既有 phone-safe schema：`/api/status`、`/api/diagnostics`、`phone_readiness`、`command_safety`、`phone_offline_resume_readiness` 等，不发明机器人状态。
3. 用 robot compatibility fence 保护 `trashbot.remote.v1`：手机静态 metadata 或新 static contract 不触发 action、不 ACK、不推进 cursor、不把 ACK 当 delivery success。
4. 同步 `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`，确保 docs 反映手机入口和证据边界。

## 责任 Owner

- `full-stack-software-engineer`：主责手机 PWA entrypoint、静态资源、离线 shell、fixture/smoke helper、手机产品文档同步。
- `robot-software-engineer`：主责 remote bridge/operator compatibility fence，确认新增静态入口 contract 不污染 command/status/ack envelope。
- `product-okr-owner`：本次启动阶段只负责 PRD、验收口径、owner 边界和 sprint 留档；最终收口时复核 OKR 数字和证据边界。

## 阻塞和风险

- 当前没有真实手机设备、真实 iPhone/Android 浏览器安装提示、真实 4G/SIM、真实公网云或 HIL；本轮只能形成 software proof。
- `mobile/web/` 不能把 fixture 或 fallback 文案伪装成实时机器人状态；所有状态必须来自 phone-safe schema 或明确标为离线样例/测试 fixture。
- service worker 或离线 shell 不得缓存 `/api/*`、robot command routes、ACK routes、diagnostics 或任何非 GET 控制流量。
- ACK 只能表示 command accepted/processing evidence，不代表 delivery success、Nav2/fixed-route success、WAVE ROVER movement 或 HIL。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后必须补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 最终收口时才允许按证据更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
