# Sprint 2026.05.13_13-14 Mobile Device Acceptance Readiness Gate - Side2Side Check

## 用户价值和产品北极星

北极星：普通手机用户不需要理解 ROS2、ACK、PWA、云探针或硬件调试，也能从手机首屏知道当前是否可安全发车、为什么不能发车、应该如何恢复或交给支持处理。

本轮价值：把“真实手机/browser/production app 尚未验收”从 final 里的风险列表前移到用户首屏，让用户和售后都能看到明确的 blocked-by-design 状态，同时不因为诊断信息存在就误开 Start/Confirm/Cancel。

## OKR 映射

- Objective 4 KR1：手机最小流程增加“手机验收准备”首屏状态。
- Objective 4 KR4：远程诊断/支持包可复述该 readiness，帮助区分手机验收缺口和机器人/云问题。
- Objective 4 KR5：普通用户看到中文恢复建议和动作阻塞原因，不需要命令行、SSH 或 ROS2 知识。
- Objective 4 KR7：phone-first UI 继续保持首屏可读和动作 fail-closed，但只声明 Docker/local software proof。

## KR 拆解或更新

- KR1：从“能确认流程”推进到“能解释手机设备/browser 验收准备状态”。
- KR4：从“诊断包可复制”推进到“诊断和支持入口在 primary actions blocked 时仍可见”。
- KR5：从“异常提示可读”推进到“真实设备、production app、PWA install prompt 缺口可读”。
- KR7：从“首屏 action/cloud/operation readiness”推进到“首屏 device acceptance readiness”。

## 本轮核心抓手

1. 手机首屏新增“手机验收准备”面板。
2. 缺真实手机/browser、production app 或真实 PWA install prompt 时，Start/Confirm/Cancel fail closed。
3. Robot metadata-only fence 证明 readiness 字段不触发 backend action、不 POST ACK、不推进 cursor。
4. OKR 只保守上调 Objective 4，不扩大证据边界。

## 需要做什么

本轮已完成：

- Task A：Full-stack 完成 mobile UI gate、fixture、static smoke 和 mobile user flow 文档同步。
- Task B：Robot 完成 remote bridge/protocol metadata-only compatibility fence 和接口文档同步。
- Task C：Product 完成 sprint closeout、OKR 和 process log 收口。

后续需要另开 sprint：

- 真实手机设备/browser 验收。
- production app 或可安装入口验收。
- 真实云/4G 与 production DB/queue 外部证据。

## 优先级和验收口径

优先级：P0，Objective 4 当前最低进度的用户触点缺口。

验收口径：

- 手机首屏能显示设备/浏览器验收准备状态、阻塞原因、恢复建议、证据边界和 ACK 语义。
- 缺真实手机/browser、production app 或真实 PWA install prompt 时，Start/Confirm/Cancel 保持禁用。
- Diagnostics 和 Support Handoff 保持可见。
- metadata-only readiness response 不触发机器人动作、不 POST ACK、不推进或持久化 cursor。
- 文档与 OKR 只声明 `software_proof_docker_mobile_device_acceptance_readiness_gate`。

## 对应责任 Engineer

- `full-stack-software-engineer`：手机 UI、fixture、static smoke、`docs/product/mobile_user_flow.md`。
- `robot-software-engineer`：remote bridge/protocol metadata-only fence、`docs/interfaces/ros_contracts.md`。
- `product-okr-owner`：OKR、process log、sprint closeout。

## 风险、阻塞和证据链

已补齐证据链：

- Full-stack mobile static smoke：`Ran 11 tests OK`。
- Full-stack `py_compile`：OK。
- Full-stack scoped diff check：OK。
- Robot remote bridge/protocol unittest：`Ran 85 tests OK`。
- Robot `py_compile`：OK。
- Robot scoped diff check：OK。

仍未补齐：

- 真实手机设备/browser。
- production app。
- 真实 PWA install prompt。
- 真实云/4G。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实送达。

## 需要创建或更新的 sprint 文档

本轮需要并已创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

本轮需要并已更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
