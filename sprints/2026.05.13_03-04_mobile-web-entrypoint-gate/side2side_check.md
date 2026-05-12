# Sprint 2026.05.13_03-04 Mobile Web Entrypoint Gate - Side2Side Check

## 验收结论

本轮 Product 收口通过。`mobile/web/` 已从 README 脚手架推进为 dependency-free PWA 静态入口，Full-stack worker 的静态 smoke 与 operator gateway targeted tests 通过；Robot worker 的 compatibility fence 证明 mobile web / PWA metadata 不会污染 robot command/status/ack envelope。

证据边界为 `software_proof_docker_mobile_web_entrypoint_gate`。这不是真实手机设备、production app、真实云、4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证明。

## 用户价值核对

- 手机用户现在有独立 `mobile/web/` 入口，不再只依赖 onboard fallback 内嵌页面。
- 首屏围绕 readiness、command safety、offline/resume、任务流程、Diagnostics 和 Support Handoff 展示 phone-safe copy。
- Start Delivery、Confirm Dropoff、Cancel 默认 fail-closed；blocked、offline、pending ACK、manual takeover 时保持禁用。
- Diagnostics 和 Support Handoff 在主操作 blocked 时仍可达，便于售后和工程支持收集脱敏上下文。

## OKR 映射核对

- Objective 4 KR1：手机端最小流程有独立静态入口和 smoke contract。
- Objective 4 KR4：入口消费诊断最小数据包和 phone-safe support/diagnostics 摘要。
- Objective 4 KR5：用户不需要命令行、ROS2、串口或 raw JSON 即可理解阻断原因和恢复路径。
- Objective 4 KR7：形成 PWA shell、manifest、service worker、offline shell 和静态 smoke；真实手机设备验收仍未完成。
- Objective 5：仅作为兼容护栏，`trashbot.remote.v1` command/status/ack 语义未改变。

## Side-by-side 对照

| 计划验收项 | 实际证据 | 结论 |
| --- | --- | --- |
| `mobile/web/` dependency-free PWA entrypoint | 新增 `index.html`、CSS、JS、manifest、service worker、offline shell、icons | 通过 |
| 只消费 phone-safe schema，不发明机器人状态 | `mobile/test_mobile_web_entrypoint.py` 覆盖 schema 消费、fixture 标记和敏感字段边界 | 通过 |
| 主操作按钮 fail-closed | static smoke 覆盖 blocked/offline 状态主操作禁用；文档同步按钮启用条件 | 通过 |
| service worker 不缓存控制流量 | static smoke 覆盖 `/api/*`、`/robots/*`、command/ACK/diagnostics/non-GET bypass | 通过 |
| remote bridge metadata-only 不触发 robot action | Robot targeted tests `Ran 60 tests in 30.370s OK` | 通过 |
| 文档同步 | `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md` 已更新 | 通过 |

## 证据缺口

- 未做真实 iPhone/Android 浏览器、真实 PWA 安装提示或手机设备验收。
- 未接真实公网云、HTTPS/TLS、真实 4G/SIM、production DB/queue 或 OSS/CDN 实流量。
- 未接 ROS2 runtime、Nav2/fixed-route、WAVE ROVER、真实串口、HIL 或真实送达。
- Browser plugin / local Chromium 不可用，Full-stack worker 未做真实浏览器截图验收。
