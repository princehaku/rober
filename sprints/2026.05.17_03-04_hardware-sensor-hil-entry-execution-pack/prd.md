# Sprint 2026.05.17_03-04 Hardware Sensor HIL-entry Execution Pack - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

北极星：让普通手机用户可以把垃圾交给低成本 ROS2 小车，并获得可理解、可追溯、可支持的送达体验；系统必须把真实硬件证据、软件 proof 和用户可见状态分清楚。

本轮用户价值：现场支持和工程同学不再靠聊天记录追问“2D LiDAR / ToF 到底还缺什么”，而是在 PC gate、Robot diagnostics 和 mobile/web 只读 panel 中看到同一份 HIL-entry execution pack。该 pack 只用于准备真实硬件 HIL-entry，不触发小车控制，不承诺已采购、已安装或已通过。

## 2. OKR 映射

- Objective 1：主映射。PR #5 要求单目 + 2D LiDAR + ToF 安全环和参数化硬件材料；本轮把 readiness review 推进为 HIL-entry execution pack，帮助真实硬件协议和传感器准入链路进入可执行准备。
- Objective 4：次映射。mobile/web 增加只读解释 panel，让普通手机入口可以看到安全、可理解的硬件准入准备状态，同时不暴露 raw JSON、串口、vendor 原文、路径、凭证或控制语义。
- Objective 5：不推进。Objective 5 约 66% 数值最低，但 Docker-only 主机缺公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/migration；本轮不是 Objective 5 external proof。

## 3. KR 拆解或更新

Objective 1 相关 KR：

- KR1/KR2/KR3：不改 WAVE ROVER UART JSON 控制和 feedback 真实实现，不新增硬件通过声明。
- KR4：新增或延续 execution-pack gate 的 focused unit coverage，验证 fail-closed material boundary。
- KR5：要求 HIL-entry execution pack 输出参数化材料字段，不把 SKU、设备路径、阈值、frame id、安全策略写死成单一硬件事实。

Objective 4 相关 KR：

- KR3/KR8/KR9：继续固化单目 + 2D LiDAR + ToF 安全环的量产约束和参数化扩展边界。
- KR5/KR7：手机端只显示用户/支持人员可读摘要；真实手机/browser 验收仍是 `not_proven`。

## 4. 本轮核心抓手

产品抓手是 `hardware_sensor_hil_entry_execution_pack`，把上一轮 readiness review 的“还缺材料”转成下一次 HIL-entry 的执行包：

- controlled HIL-entry manifest：说明下一次真实上车验证应收集哪些材料。
- material templates：拆出 SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 模板。
- command summary：只给安全的 first-run / rerun command 摘要，不暴露 raw command、raw JSON、串口、路径或凭证。
- owner handoff：明确 Hardware、Robot、Full-stack 的后续责任边界。

## 5. 需要做什么

### Hardware Infra Engineer

创建 `hardware_sensor_hil_entry_execution_pack` PC gate，输入上一轮 readiness review artifact/summary，输出 artifact 与 summary。必须先读 `docs/vendor/VENDOR_INDEX.md`；涉及 WAVE ROVER / Orange Pi / UART JSON 的资料来源只作为 source boundary，不作为真实 HIL 或采购证据。

### Robot Platform Engineer

在 diagnostics 中新增 metadata-only consumer，支持 explicit ref、env、latest status、nested diagnostics summary。缺 summary、unsupported schema、weak boundary、success claim、unsafe raw field 时 fail closed。

### User Touchpoint Full-Stack Engineer

在 mobile/web 增加只读“传感器 HIL 执行包” panel。只展示 schema/status、safe `evidence_ref`、material templates、owner handoff、safe command summary、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. 优先级和验收口径

P0：

- PC gate 生成 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate` artifact/summary。
- Robot diagnostics metadata-only 消费该 summary，并保持控制路径不变。
- mobile/web 只读 panel 可渲染该 summary，并保持 Start Delivery / Confirm Dropoff / Cancel gating 不变。

P1：

- 文档同步更新 `pc-tools/README.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- 验证命令只做围栏：`py_compile`、focused unittest、`node --check`、required `rg`、scoped `git diff --check`。

不验收：

- 真实 2D LiDAR / ToF 到货、安装、接线、供电、标定。
- 真实 WAVE ROVER、真实串口、UART feedback、HIL、Nav2/fixed-route、route/elevator pass、delivery success。
- 真实手机/browser、production app、PWA prompt。
- Objective 5 external proof。

## 7. 风险、阻塞和证据链缺口

- 最大风险：execution pack 被误写成“ready/pass/complete”。所有 surfaces 必须保留 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 真实硬件材料仍缺：SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。
- Objective 5 blocker 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/migration。
- mobile/web 只能证明本地软件渲染和 fail-closed copy，不证明真实手机或 production app。
- vendor 文件是本地资料来源，不是采购、安装、标定或 HIL-entry 证据。
