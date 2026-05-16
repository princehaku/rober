# Sprint 2026.05.16_18-19 Hardware Sensor HIL-entry Config Precheck - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：让硬件、Robot、手机端和 Product 对“传感器 HIL-entry 前置条件”有同一套可检查语言。普通用户只看到安全、可解释、不会误导的只读状态；现场支持看到缺哪些材料；工程同学必须在配置里显式表达 sensor count、thresholds、frame IDs、safety policy 和证据引用，不能把单一 SKU 假设写死。

产品北极星：`rober` 是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。为了从 software proof 走向真实 HIL 和现场交付，必须先建立硬件传感器配置进入 HIL 的 fail-closed contract，避免“默认硬件集”“mandatory sensor baseline”“手机端展示”和“Robot diagnostics”互相漂移。

## 2. 背景证据

- 当前 `OKR.md` 4.1 中 Objective 5 约 66%，数值最低；Objective 1 约 74%，Objective 2 / Objective 3 约 79%，Objective 4 约 87%。
- 本机只有 Docker，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；Objective 5 继续堆本地 metadata 不再形成有效进展。
- GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` review 指出三类问题：P1 default hardware set 与 mandatory sensor baseline 不一致；P2 OKR lowest-objective claim 不一致；P2 mandatory sensor assumptions 缺 `docs/vendor/` source attribution。
- 最新 sprint `2026.05.16_17-18_hardware-baseline-source-alignment` 已完成 source-alignment gate，但结论明确：local vendor coverage 不证明 2D LiDAR / ToF 已采购、安装、接线、标定、HIL 或 field pass。

## 3. OKR 映射

- Objective 1：硬件协议可信底盘。本轮直接服务 HIL-entry 前置配置可信度，目标是让未来 2D LiDAR / ToF 进入 HIL 前必须携带参数化 config、证据引用和安全策略。
- Objective 4：手机用户体验与低成本量产边界。本轮让手机端只读展示 HIL-entry config precheck 摘要，用普通用户可理解的文案解释“未证明”和“下一步材料”，同时不打开任何控制动作。
- Objective 5：云中转 + OSS/CDN 数据通路产品化。本轮不推进 Objective 5，因为缺真实外部证据；文档必须说明 stop rule，避免最低 Objective 口径不一致。

## 4. KR 拆解或更新

- O1 KR HIL-entry config：新增 future HIL-entry sensor config precheck，覆盖 sensor count、thresholds、frame IDs、safety policy、evidence refs 和 vendor/source boundary。
- O1 KR hardware-source discipline：2D LiDAR / ToF 仍必须从 `docs/vendor/VENDOR_INDEX.md` 或真实采购/安装/标定材料引用，不允许把 product target 写成 installed/proven hardware。
- O4 KR phone-safe diagnostics：mobile/web 只读展示 precheck status、missing config/materials、owner next action、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- O4 KR control safety：Start / Confirm Dropoff / Cancel gating 保持不变；precheck panel 不能改变 primary action authorization。

## 5. 本轮核心抓手

建立 `trashbot.hardware_sensor_hil_entry_config_precheck.v1` / `trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1`，并用四条互不重叠的工作线落地：

- Hardware：PC gate + test，定义参数化完整性与证据引用检查。
- Robot：diagnostics metadata-only consumer，缺失、unsupported、unsafe、success claim 必须 fail closed。
- Full-stack：mobile/web 只读 panel，copy/export whitelist-only。
- Product：实现完成后更新 OKR、进度日志和 sprint 收口。

## 6. 需要做什么

1. 定义 HIL-entry config precheck 输入与输出。
2. 要求 future sensor config 至少表达：
   - sensor count：2D LiDAR 数量、ToF channel count 或 coverage。
   - thresholds：near-field / safety / confidence 阈值必须参数化。
   - frame IDs：传感器 frame、base frame、可选 mount frame 必须显式配置。
   - safety policy：missing config、missing evidence、unsafe copy、unsupported schema、success claim 的 fail-closed 策略。
   - evidence refs：source、procurement、install/wiring、calibration、HIL-entry material 必须作为引用或缺口列出。
3. Robot diagnostics 和 mobile/web 只能消费 summary，不读取 raw artifacts，不暴露硬件细节、路径、凭证、raw JSON、ROS topics 或控制面字段。
4. Product closeout 必须按实际结果更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但只能使用 software proof 口径。

## 7. 优先级和验收口径

P0：

- Contract 名称、schema、evidence boundary、fail-closed status 固化。
- PC gate 能拒绝硬编码单一 SKU / 单一 sensor count / 缺 thresholds / 缺 frame IDs / 缺 safety policy / 缺 evidence refs。
- Robot diagnostics 和 mobile/web 不改变 primary actions。

P1：

- 文档同步到 `pc-tools/README.md`、`docs/product/production_hardware_boundary.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- Product closeout 清楚说明 Objective 5 stop rule 和 Objective 1 / Objective 4 的 software-proof 进展边界。

验收通过只代表：

- `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

验收不得代表：

- 真实 WAVE ROVER/UART/HIL。
- 真实 2D LiDAR / ToF 采购、安装、接线、供电、标定或 field pass。
- 真实手机/browser 或 production app。
- Objective 5 external proof。

## 8. 对应责任 Engineer

- Hardware Infra Engineer：Task A。
- Robot Platform Engineer：Task B。
- User Touchpoint Full-Stack Engineer：Task C。
- Product Manager / OKR Owner：Task D。

实现阶段必须按 2-4 个并行 worker 启动；本轮计划选择 4 个 worker，因为文件范围互不重叠，且需要同时覆盖 PC gate、Robot consumer、mobile consumer 和 Product closeout。

## 9. 风险、阻塞和需要补齐的证据链

- 真实硬件风险：当前没有真实 WAVE ROVER/UART/HIL packet，也没有 2D LiDAR / ToF source/receipt/install/wiring/power/calibration/HIL-entry 材料。
- 文案风险：手机端容易把 precheck ready 误读成 hardware ready，必须用 `not_proven` 和 `delivery_success=false` 固定边界。
- 配置风险：如果 config contract 只检查存在字段而不检查参数化语义，仍可能让单一 SKU 硬编码进入 HIL-entry。
- O5 风险：Objective 5 仍最低，但缺外部材料，不能通过本轮硬件 config software proof 上调。

需要补齐的真实证据链：

- 2D LiDAR / ToF SKU/source/receipt。
- 安装、接线、供电、电气安全材料。
- 标定结果与 frame tree 校验。
- 真实 HIL-entry logs。
- 后续 route/elevator field pass。
- 真实手机设备/browser 现场验收。
- Objective 5 外部公网/4G/OSS/CDN/DB/queue/worker/migration 材料。

## 10. 需要创建或更新的 sprint 文档

本规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

