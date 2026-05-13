# Sprint 2026.05.14_02-03 Mobile Current PWA Browser Proof Refresh - PRD

## 用户价值

普通用户与支持人员看到的是当前 `mobile/web/` 第一屏，而不是 2026-05-13 早些时候的旧面板组合。最近几轮已新增恢复决策、终端动作二次确认、手机设备证据采集、真实手机验收交接会话和 PWA 安装提示证据；如果浏览器 proof 仍只验证旧的浏览器验收包，就无法证明当前首屏没有布局、可点击区域、copy 泄漏或动作误放行回归。

本轮要把本地 Chromium-family browser proof 刷新到当前 PWA 形态，让 Docker-only 主机也能产出可复查的截图/JSON evidence，服务下一步真实手机或 production app 验收。

## OKR 映射

- Objective 4 / KR1：手机端最小流程仍围绕选择/确认垃圾站、确认已放入垃圾、一键发车、查看状态和处理异常。
- Objective 4 / KR5：普通用户不接触 ROS2、串口或硬件调试，也能知道当前为何不能控制、下一步需要什么证据。
- Objective 4 / KR7：首屏 UI 必须适配主流移动尺寸、可点击区域足够、文案中文优先、主操作 fail closed。

Objective 5 不作为本轮主线。理由是缺少真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料；继续叠加本地 O5 metadata 会重复消费同一外部 blocker。

## 范围

本轮交付一个当前 PWA browser proof refresh：

1. `phone_browser_acceptance_gate.py` 覆盖当前首屏关键面板：
   - 三步主路径。
   - 恢复决策。
   - 终端动作二次确认。
   - 手机设备证据采集。
   - 真实手机验收交接会话。
   - PWA 安装提示证据。
   - 浏览器验收包、Diagnostics、Support Handoff 和 ACK 文案。
2. browser gate 输出 summary 中声明新的 refresh boundary，并保留旧 boundary 兼容信息。
3. 运行 gate 产出 `evidence/` 下的 JSON/PNG/summarized proof。
4. 更新 mobile 文档和接口文档，保持 metadata-only 边界。
5. 更新 OKR 与 sprint 收口，若只有 local browser proof refresh，Objective 4 只能小幅或不调整。

## 非目标

- 不证明真实 iPhone/Android。
- 不证明 production app。
- 不证明真实 PWA install prompt 或真实用户选择。
- 不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消或真实送达。

## 验收口径

- Gate 必须在 390x844 与 768x900 两个 viewport 通过。
- Start、Confirm Dropoff、Cancel 必须继续 disabled / fail closed。
- Diagnostics、Support Handoff、copy acceptance bundle 或等价 phone-safe copy 入口保持可见。
- 当前新增首屏面板的关键文案、boundary 和 ACK 语义必须可见。
- 可见文本不得包含 token、Authorization、OSS AK/SK、DB/queue URL、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum 或完整 artifact。
- Robot compatibility fence 必须确认 browser proof refresh metadata 是 metadata-only，不触发 backend action、ACK POST、cursor advance/persistence 或 delivery success。
