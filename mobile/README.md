# mobile/ — 用户手机 PWA / 触点入口

本目录是 `ros_rbs` 的 **用户手机端部署单位**：把机器人能力产品化成手机能操作、能看状态的入口。

> 当前状态：sprint `2026.05.13_01-02_codebase-restructure-four-tier` 的 Phase 2B 已建立脚手架；真正的前端资源（HTML/CSS/JS）会在 Phase 5 由 `full-stack-software-engineer` 从 `operator_gateway_static.py` 内嵌字符串里抽出来搬到这里。

## 用途（What lives here）

- **手机浏览器入口**（首选）：用户手机直连云端 `https://cloud-relay/api/*` 即可使用，不需要装 app、不需要 SSH、不需要懂 ROS2 topic。
- **未来 native app**（次选）：可基于本目录的 PWA 资产打包 Capacitor / Tauri / Cordova 等 native 壳，复用同一份 UI。

## 子目录

| 目录 | 用途 | P5 完成后承接 |
| --- | --- | --- |
| `mobile/web/` | PWA 前端静态资源 | `index.html` / 抽出的 CSS / JS / `manifest.webmanifest` / `service-worker.js` / `offline.html` / icons |
| `mobile/design/` | 设计稿、原型、phone-safe 中文文案 contract | Figma 链接、文案校对清单、可访问性规范 |
| `mobile/fixtures/` | 离线 fixture / 手机端浏览器验收用 mock 数据 | phone-safe JSON sample、断网回放数据 |

## 部署目标（Deployment target）

- **设备**：CEO + 操作员的安卓 / iOS 手机浏览器。
- **网络**：手机端 4G / Wi-Fi → 公网 → `cloud-relay`（4C8G 公网部署单位）→ 机器人端 4G 反向连接。
- **运行环境**：现代浏览器（Chrome / Safari / Edge 最近 2 个大版本）；不依赖 native API，但优先利用 PWA 离线缓存 + service worker 提高弱网体验。

## 运行时契约（Runtime contracts）

- **消费方**：手机浏览器通过 `https://cloud-relay/api/*` 拉 phone-safe JSON。
- **schema**：`trashbot.phone_readiness.v1`、`trashbot.command_safety.v1`、`trashbot.phone_offline_resume_readiness.v1` 等字段、值域、`evidence_boundary` **完全由 `cloud-relay/` 维护**，mobile 端只消费、不发明。
- **错误语义**：所有失败必须有可读中文说明、错误码和恢复建议（"重试"、"等待机器人重新上线"、"联系管理员" 等），不允许吞掉错误。
- **控制动作**：所有发送到机器人的命令（如 `collect` / `confirm_dropoff`）必须有二次确认、视觉反馈、失败提示和可恢复路径；涉及真实运动的命令必须和 hardware/robot-engineer 对齐安全边界。

## 当前 P1+P2B 状态

- 仅创建 README 脚手架，**不搬任何前端代码**。
- `operator_gateway_static.py` 内嵌的 HTML/CSS/JS 留在 onboard `ros2_trashbot_behavior` 包内，等 P5 完成 cloud-relay 整合后再抽出来。
- 手机端验收 gate：`pc-tools/evidence/phone_browser_acceptance_gate.py`（与本目录无 import 耦合，仅文档引用）。

## Agent 工作纪律

- 修改本目录前必读 `AGENTS.md`、`OKR.md`、对应 sprint 文档；涉及 phone-safe schema 字段必读 `docs/interfaces/`（若有）和 cloud-relay 测试代码。
- UI 不得发明机器人状态：所有显示的字段必须来自 cloud-relay 输出的 phone-safe JSON，不允许前端 hardcode "模拟状态"。
- 控制按钮必须有确认、反馈、失败提示和可恢复路径。
- 中文注释比例 >20%，注释解释"为什么"而非"做什么"。

## 路线图（Roadmap）

| 阶段 | 工作 |
| --- | --- |
| 本 sprint P2B（当前） | README 脚手架 |
| 本 sprint P5 | 从 `operator_gateway_static.py` 抽出 HTML/CSS/JS 到 `mobile/web/`；维持 phone-safe schema 不变 |
| 下一个 sprint | PWA 离线 service-worker、断网弱网体验优化、操作日志面板 |
| 后续 | 远程控制安全边界（紧急停止、围栏、地理围栏）、native 壳打包 |
