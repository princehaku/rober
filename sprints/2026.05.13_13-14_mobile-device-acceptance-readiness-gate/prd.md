# Sprint 2026.05.13_13-14 Mobile Device Acceptance Readiness Gate - PRD

## 用户价值

普通手机用户需要知道“当前手机入口离可真实使用还差什么”，而不是只看到云、ACK、诊断等工程状态。最近几轮已经让手机端能显示 action feedback、cloud readiness 和 operation log，但 final 文档反复留下同一类风险：没有真实手机设备/browser、production app、真实 PWA install prompt 和真实云/机器人证据。本轮把这些差距变成首屏可读的 readiness 摘要，降低误操作和误判。

## OKR 映射

- Objective 4 KR1：手机最小流程增加“设备/浏览器验收准备状态”。
- Objective 4 KR4：远程诊断最小数据包可以复述该 readiness，帮助支持判断当前是手机验收缺口还是机器人/云问题。
- Objective 4 KR5：普通用户不用理解 ROS2、ACK、PWA、浏览器 gate 或 production app 差异，也能看到当前不可放行的原因。
- Objective 4 KR7：手机端 UI 继续走 phone-first 首屏可读体验，但本轮仍只声明 Docker/local software proof。

## 范围

### In Scope

1. `mobile/web/` 增加 `mobile_device_acceptance_readiness` 消费和展示。
2. `mobile/fixtures/mobile_web_status.fixture.json` 增加 blocked-by-design 示例。
3. `mobile/test_mobile_web_entrypoint.py` 增加静态 smoke 断言，确保 panel 可见、fail closed、无敏感词、ACK 不等于 delivery success。
4. `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 同步 schema 和边界。
5. robot compatibility fence 覆盖 metadata-only `mobile_device_acceptance_readiness` / `phone_device_acceptance_readiness` / `mobile_browser_acceptance_readiness`。

### Out of Scope

- 不做真实手机设备验收。
- 不做 production app、账号、登录或应用商店打包。
- 不做真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 不新增广泛测试矩阵。

## 验收口径

1. 手机首屏能显示设备/浏览器验收准备状态、阻塞原因、恢复建议、证据边界和 not-proven 列表摘要。
2. `primary_actions_enabled=false`、缺失 readiness 或 `production_app_ready=false` 时，Start/Confirm/Cancel 继续禁用；Diagnostics/Support 仍可见。
3. robot compatibility fence 证明 metadata-only response 不触发机器人动作、不 POST ACK、不推进或持久化 cursor。
4. 文档和 OKR 只声明 `software_proof_docker_mobile_device_acceptance_readiness_gate`，不声明真实手机/browser 或 production app 通过。

## 责任分工

- Task A / `full-stack-software-engineer`：实现手机 UI gate 和静态 smoke。
- Task B / `robot-software-engineer`：实现 metadata-only compatibility fence。
- Task C / `product-okr-owner`：收口 sprint、OKR 和进度日志。
