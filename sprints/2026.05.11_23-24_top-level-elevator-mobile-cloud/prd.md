# Sprint 2026.05.11 23-24 Top-Level Elevator/Mobile/Cloud Redesign - PRD

## 1. 业务诉求

CEO（用户）在 2026-05-11 23:59 给出顶层方向调整：

1. **跨楼层送垃圾必须做**：进出电梯不再是 H2 受控场景，而是 MVP 必须能力。小车要能识别电梯门状态、进入电梯、语音求助按楼层、识别到达目标楼层、目标楼层开门时驶出。
2. **手机端必须美观且能直接使用**：不再接受"phone-first dependency-free HTML"。普通用户拿到手机能立刻看懂、立刻使用。
3. **CEO 提供 4G 中转服务端**：`ssh root@14.103.37.144 -p 7878`，4C 8G 无 GPU，作为 4G 数据通信中转。
4. **CEO 提供 OSS + CDN**：阿里云 OSS bucket `bytegallop`（region `oss-cn-hangzhou`），CDN `https://cdn.bytegallop.com/rober/`，用于数据中转。
5. **本次是顶层设计，无需多个子 agent 干活**：产品方向、OKR、产品 contract 升级，不写代码、不改硬件。

## 2. 北极星调整

旧北极星把电梯能力放在"H2/高阶场景可纳入"。

新北极星调整为：

- 跨楼层 trash delivery 是 MVP 范围。小车必须能在受控楼宇内识别电梯门状态、进入电梯、播放语音求助、识别目标楼层并安全驶出。
- 手机端是普通用户唯一入口，必须美观、可直接使用、不依赖命令行或 SSH。
- 4G 路径由云端中转，本地 operator gateway 仅作 fallback；4G 链路只走 behavior-level contract，不暴露 `/cmd_vel`。

人工协助（请旁人帮忙按电梯按钮）仍然是产品边界，不在本轮变更。小车不按按钮、不改造电梯、不新增机械臂。

## 3. Objective 与 KR 调整

### Objective 2：可恢复送垃圾任务闭环

- KR6 从"H2/受控场景"改为"MVP 必须"：行为状态机必须覆盖电梯子流程（等待开门 -> 进入电梯 -> 语音求助 -> 等待目标楼层 -> 目标楼层开门驶出），失败和超时必须有人工接管路径。
- 不抬当前实机完成度。

### Objective 4：感知模块产品化

- KR6 从"H2/受控场景"改为"MVP 必须"：感知 contract 必须覆盖电梯门开/关、是否进入电梯、目标楼层到达证据、目标楼层开门可驶出证据。
- 优先用现有相机/语音/日志证据，不默认新增硬件。
- 不抬当前实机完成度。

### Objective 5：手机用户体验与低成本量产边界

- KR6 从"H2/受控场景"改为"MVP 必须"：手机端必须能解释电梯流程、人工协助边界、失败原因，并触发语音求助提示。
- **新增 KR7：手机端 UI 美观可直接使用**。
  - 视觉层级清晰，操作主路径不超过 3 步。
  - 配色、字号、间距、状态色保持一致，不再使用 dependency-free 极简灰白页面。
  - 适配 iOS Safari、Android Chrome 主流尺寸。
  - 状态卡片、按钮、错误提示均有可读语言版本（中文优先），不依赖 raw JSON。
  - 首次进入有引导或自解释，不需要任何 README/SSH/命令行。

### 新增 Objective 6：4G 云中转 + OSS/CDN 数据通路

**目标说明**：让小车通过 4G 走云端中转完成手机用户控制与数据回传，不依赖手机和小车处于同一 WiFi。同时把图片/快照/任务记录类大对象通过 OSS + CDN 沉淀，4G 中转节点不承担大文件带宽。

**Key Results**：

- KR1：明确云中转服务端最小契约（commands/status/ack），HTTPS、outbound polling 优先，幂等 + bearer token 鉴权，不暴露 `/cmd_vel`。
- KR2：服务端基线规格（4C 8G 无 GPU）写入 `docs/product/cloud_4g_infrastructure.md`，包含 SSH 端口、网络方向、防火墙策略和容量边界。
- KR3：OSS 写入策略明确：bucket `bytegallop`，对象前缀 `rober/`，可读不可枚举，写入路径包含 `task_id`/`route_id`/`timestamp`，超 90 天可回收。
- KR4：CDN `https://cdn.bytegallop.com/rober/` 只作为公开只读视图入口，diagnostics 引用必须以 URL 形式给出，不在小车本地暴露密钥。
- KR5：凭证管理 contract：`.env` 不入仓库，`.env.example` 仅占位；服务端、CI、上车机器人均通过环境变量注入；密钥泄露走 rotate 流程。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须有 graceful degradation：本地操作仍可用，状态可恢复，不丢任务。

## 4. 手机端美观与可直接使用的产品 contract

详见新增文档 `docs/product/mobile_ui_quality.md`。本 PRD 写明硬要求：

1. **可读性**：所有状态、按钮、错误提示必须有中文文案；不允许向普通用户暴露 raw JSON 或 ROS topic 名称。
2. **响应式**：iPhone 12 / 13 / 14 / 15 / Pixel 6/7 主流尺寸，最小可点击区域 44pt。
3. **状态卡片**：任务状态、机器人位置、电梯子状态、视觉证据链状态、硬件 proof 状态都用卡片展示，使用一致配色和图标。
4. **主操作主流程**：放垃圾 -> 选择目标 -> 出发 -> 跟踪状态 -> 完成 / 接管，主流程不超过 3 个核心按钮。
5. **不可降级**：本地 operator gateway 的 phone-first HTML 仅作 fallback；正式手机入口必须是美观的 web/app 页面。

## 5. 4G 中转、OSS、CDN 接入边界

- **手机 ↔ 云**：HTTPS + bearer token；命令、状态、ACK 走 JSON contract（沿用 `trashbot.remote.v1`）。
- **小车 ↔ 云**：outbound polling（HTTP / 后续 MQTT/WebSocket），不接受 inbound。
- **小车 ↔ OSS**：仅写自身相关对象，前缀 `rober/<robot_id>/<date>/<task_id>/`；写入使用 STS 临时凭证或受限 AK，避免长期主 AK 直放小车。
- **手机/支持 ↔ CDN**：通过 CDN URL 读取公开图片/快照；私有数据走云端 API 网关 + bearer。
- **服务端运维边界**：SSH 端口 `7878`，仅运维使用；产品功能均走 HTTPS API；服务端不部署机器人控制代码，只做状态/命令/ACK 中转 + OSS 推送 helper。

## 6. 非目标（本轮不做）

- 不写 4G 云端服务实际代码、Dockerfile、部署脚本。
- 不写小车侧 OSS 上传客户端代码。
- 不抬任何 Objective 的实机完成度。
- 不修改 `src/` 目录任何文件。
- 不修改 `docs/vendor/`、`docs/hardware/`、`docs/interfaces/`、`docs/acceptance/`、`docs/navigation/`、`docs/vision/`、`docs/superpowers/` 中任何文件。
- 不对外承诺已能开放楼宇、复杂人群电梯、高峰期电梯或无人看护场景。
- 不对外承诺手机 UI 已经美观可发布（只承诺 contract 已落地）。

## 7. 验收口径

1. `OKR.md` 包含"电梯 MVP 必须"、"手机美观必须"、"Objective 6 4G/OSS/CDN" 三类关键词与对应章节。
2. `docs/product/elevator_assisted_delivery.md` 顶部状态从 `H2/受控场景产品方向` 改为 `MVP/必须实现 + 受控场景验证`。
3. `docs/product/mobile_user_flow.md` 明确手机端"美观、能直接使用"是强制 product contract。
4. `docs/product/remote_4g_mvp.md` 引用云中转服务端 `14.103.37.144:7878`（只写端口和方向，不写密码）。
5. `docs/product/cloud_4g_infrastructure.md` 完整描述服务端规格、OSS bucket、CDN base URL、凭证管理。
6. `docs/product/mobile_ui_quality.md` 给出美观可用性的量化口径。
7. `.env.example` 给出占位变量，`.gitignore` 排除 `.env`。
8. 任何 tracked 文件不出现 `OSS_ACCESS_KEY_SECRET` 的真实值字符串 ``。
9. Sprint 六件套完整存在，scoped `git diff --check` 通过。
