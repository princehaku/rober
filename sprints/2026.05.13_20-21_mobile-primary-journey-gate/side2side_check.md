# Sprint 2026.05.13_20-21 Mobile Primary Journey Gate - Side2Side Check

## 对照结论

本轮 PRD 目标是把手机首屏从 proof 面板堆叠推进成普通用户可理解的“三步主路径”：目标垃圾站、已放入垃圾确认、发车安全 gate。Task A 和 Task B 的返回证据满足该目标的 Docker/local software proof 口径。

| PRD/tech-plan 验收项 | 实际证据 | 结论 |
| --- | --- | --- |
| 首屏三步主路径可渲染 | Task A 更新 `mobile/web/`、fixture、entrypoint test；`mobile.test_mobile_web_entrypoint` 15 tests OK | 通过 |
| Start fail closed | Task A 覆盖缺字段、blocked、offline、pending ACK、manual takeover、未确认 load、缺 destination | 通过 |
| `/api/collect` 保留 `target` 兼容 | Task A 明确 payload 保留 `target` | 通过 |
| ACK 不写成送达成功 | Task A 文案与测试保持 accepted/processing only | 通过 |
| metadata-only 不污染 robot command/ACK/cursor | Task B remote bridge/protocol 106 tests OK，metadata 不触发 action、不 POST ACK、不推进/持久化 cursor | 通过 |
| 不改 production `remote_bridge.py` | Task B 返回明确未改 production `remote_bridge.py` | 通过 |

## 用户价值核对

用户价值：普通手机用户能先看懂“去哪里、是否已放好、现在能不能发车”，并在不能发车时看到阻塞原因，而不是面对工程 proof 面板堆叠。

产品北极星对齐：本轮只推进普通用户手机入口的理解性和安全 gate，不把本地软件证明包装成真实送达或真实生产手机端。

## OKR 映射核对

- Objective 4 KR1：三步主路径对应“选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车/查看阻塞”。
- Objective 4 KR5：普通用户不需要接触 ROS2、串口或硬件调试，也能知道当前为什么不能发车。
- Objective 4 KR7：主操作主路径保持三步，中文优先，按钮态和阻塞语义清晰。
- Objective 5：本轮没有真实外部材料，只复用 cloud/device/browser readiness 作为 O4 gate 输入，不提升 O5。

## 证据边界核对

本轮证据边界为 `software_proof_docker_mobile_primary_journey_gate`。它明确不是：

- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA install prompt。
- 真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic。
- production DB/queue、production worker 或 migration。
- Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。

`not_proven` 仍包含真实手机设备、production app、真实 PWA install prompt、真实云/4G、真实 OSS/CDN、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 和真实 delivery success。ACK 只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。

## 需要后续补齐

- 真实 iPhone/Android device behavior。
- production app 或真实 PWA install prompt。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue。
- Nav2/fixed-route、WAVE ROVER、HIL、真实投放和真实送达。
