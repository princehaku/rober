# Sprint 2026.05.13_05-06 Mobile Task Start Confirmation Gate - PRD

## 用户价值和产品北极星

用户价值：普通用户在手机上发车前，必须知道"要送到哪个垃圾站"和"我已经把垃圾放上车"，再触发任务。这个步骤降低误发车、空车发车、发错垃圾站和售后解释成本，也符合低成本量产边界：用软件确认流程替代新增传感器或复杂硬件。

产品北极星：手机是普通用户唯一入口。用户不需要理解 ROS2、topic、串口、云队列、WAVE ROVER 或 ACK 细节；手机只展示安全步骤、中文提示、当前阻塞原因和可恢复动作。

## OKR 映射

- Objective 4 KR1：补齐"选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车"的显式手机步骤。
- Objective 4 KR5：普通用户不接触命令行、不插线调试、不理解 ROS2，也能知道何时可以发车、何时被 blocked、失败时该打开诊断或等待。
- Objective 4 KR7：手机主路径继续保持中文优先、主操作不超过 3 步、按钮 fail-closed、状态可读；本轮仍只是 local/Docker software proof，不声明真实手机设备验收。
- Objective 2 guardrail：发车 payload 只能表达用户选择和确认，不把 ACK、accepted 或 processing 解释为送达成功。
- Objective 5 guardrail：payload 可以服务未来云中转，但不能要求真实云、4G、production DB/queue 或 OSS/CDN live traffic。

## 证据引用

- `OKR.md` 4.1：Objective 4 当前约 56%，主要缺口仍是 production app、真实手机浏览器/设备验收、真实 PWA install prompt、TTS/喇叭实放和量产实物验收；Objective 5 约 57%。
- `03-04 final.md`：mobile web entrypoint 已完成，但边界是 `software_proof_docker_mobile_web_entrypoint_gate`，不是 production app、真实手机浏览器/设备、真实云/4G、HIL 或真实送达。
- `03-04 tech-done.md`：`mobile/web/` 已能消费 `phone_readiness`、`command_safety`、`phone_offline_resume_readiness`，主操作必须同时满足 `command_safety` 和旧权限。
- `04-05 final.md`：cloud deployment readiness gate 完成后 Objective 5 到约 57%，Objective 4 仍保持约 56%，因为没有 real phone app/device 或 production app 新证据。
- `04-05 tech-done.md`：`software_proof_docker_cloud_deployment_readiness_gate` 仍是 Docker/local blocked readiness；ACK 仅是 accepted/processing evidence。
- `docs/product/mobile_user_flow.md` KR1/KR5/KR7 对应文案：Minimum User Journey 明确选择/确认垃圾站、放入垃圾、确认装载后开始；用户不需要 SSH、ROS2、serial tools 或硬件调试；手机端要中文优先、主路径清晰、按钮受 command safety 控制。
- `mobile/web/app.js`：当前 `submitAction()` 对 `/api/collect` 只执行 `fetchJson(ENDPOINTS[actionName], { method: "POST" })`，没有 JSON body，无法证明发车前确认垃圾站和已放入垃圾。

## 本轮 KR 拆解

### KR-A：手机发车前目标确认

验收口径：

- 首屏或发车区显示后端推荐/当前垃圾站。
- 用户可明确选择或确认垃圾站，缺少垃圾站时 Start Delivery fail closed。
- UI 文案不得暴露 raw JSON、ROS topic、串口设备、WAVE ROVER 参数或 `/cmd_vel`。

### KR-B：装载确认 gate

验收口径：

- Start Delivery 前必须显式勾选或确认"已放入垃圾"。
- 未确认装载时按钮禁用或提交被本地阻断，并展示中文原因。
- 不把该确认包装成自动传感器检测；它只是用户确认。

### KR-C：phone-safe collect payload

验收口径：

- `POST /api/collect` 使用 `Content-Type: application/json`。
- payload 至少包含 schema/version、用户选择的垃圾站标识或 label、`trash_loaded_confirmed=true`、source=`mobile_web`、client timestamp 或 idempotency-friendly client reference。
- payload 不包含 raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、硬件配置、credential、local path 或完整 diagnostics artifact。

### KR-D：双 gate 和 fail-closed 保持

验收口径：

- Start Delivery 仍必须同时满足 `command_safety.actions.start.enabled=true` 和旧权限 `can_collect=true`。
- blocked/offline/pending ACK/manual takeover、后端缺少 `command_safety`、目标未确认、装载未确认、payload 构造失败均 fail closed。
- Diagnostics 和 Support Handoff 仍可达，但不能使 Start/Confirm/Cancel 变绿。

### KR-E：ACK 语义保持

验收口径：

- UI、测试和文档必须继续写清 ACK 只代表指令 accepted/processing，不代表 delivery success。
- Robot compatibility fence 证明新增 phone payload metadata 不触发非预期 robot backend call、不 POST 错误 ACK、不推进 cursor、不持久化 cursor、不改变 command envelope。

## 优先级

P0：

- 目标垃圾站展示/确认。
- "已放入垃圾"确认。
- `POST /api/collect` phone-safe JSON payload。
- `command_safety` + 旧权限双 gate 和 fail-closed。
- ACK 文案和 robot compatibility fence。

P1：

- 目标垃圾站来源兼容后端 `phone_task_flow_readiness` 或 `phone_readiness` 中的 destination summary。
- 用户可读的阻塞原因和恢复提示。
- 静态 smoke 覆盖 payload 安全字段。

Out of scope：

- 真实手机设备、真实 iPhone/Android 浏览器验收。
- production app、账号系统、真实云、4G/SIM、OSS/CDN live traffic。
- Nav2/fixed-route 实跑、WAVE ROVER、HIL、真实送达。
- 自动判断垃圾是否真的放入、称重或传感器新增。

## 对应责任 Engineer

- `full-stack-software-engineer`：实现 UI、payload、静态 smoke、`docs/product/mobile_user_flow.md` 更新。
- `robot-software-engineer`：实现 remote bridge/protocol 兼容性测试和相关接口文档更新。
- `product-okr-owner`：收口证据、`side2side_check.md`、`final.md`、`OKR.md` 进展更新。

## 风险、阻塞和证据链缺口

- 没有真实手机设备：最终只能写 `software_proof_docker_mobile_task_start_confirmation_gate`。
- 没有真实云/4G：payload 只能证明 phone-safe local/API contract，不证明 cloud production path。
- 没有真实机器人/HIL：ACK、accepted、processing 都不能解释为送达成功。
- 后端可能尚无完整 destination schema：full-stack 需要兼容现有 `phone_task_flow_readiness`、`phone_readiness` 和安全 fallback，缺字段时 fail closed。
- 新 payload 若被 robot bridge 误解释为 command envelope，会破坏 Objective 2/5 语义；必须由 robot worker 加 compatibility fence。
