# Sprint 2026.05.16_18-19 Hardware Sensor HIL-entry Config Precheck - Pre Start

sprint_type: epic

## 1. 开始时间与目标

- 开始时间：2026-05-16 18:02 CST。
- Sprint 目录：`sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/`。
- 本轮目标：把下一步硬件传感器 HIL-entry 入口从“传感器来源对齐”推进到“参数化配置预检查 contract”，确保 sensor count、thresholds、frame IDs、safety policy 不能硬编码为单一 SKU 或单一安装假设。
- 本轮只做规划阶段文档：`pre_start.md`、`prd.md`、`tech-plan.md`。实现、测试、OKR 更新和收口文档由后续 worker 按 plan 执行。

## 2. 上轮证据与未完成项

最新 sprint `2026.05.16_17-18_hardware-baseline-source-alignment` 已完成 `software_proof_docker_hardware_baseline_source_alignment_gate`。结论是：

- 已把 PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` review 暴露的 default hardware set / mandatory sensor baseline 矛盾转成可机器验收的 source-alignment software proof。
- 已在 Robot diagnostics 和 mobile/web 里做 metadata-only、phone-safe 展示。
- 仍然不证明真实 2D LiDAR / ToF 已采购、安装、接线、供电、标定、HIL-entry、Nav2/SLAM field pass、near-field safety pass 或 delivery result。
- 仍然不证明真实 WAVE ROVER/UART/HIL、真实手机/browser 或 Objective 5 external proof。

因此本轮不得重复做 source alignment；下一步必须把 future HIL-entry sensor config 的参数化完整性、证据引用和 fail-closed 策略落成可验证 contract。

## 3. OKR 当前排序与转向理由

当前 `OKR.md` 4.1 快照：

- Objective 5：约 66%，数值最低。
- Objective 1：约 74%。
- Objective 2 / Objective 3：约 79%。
- Objective 4：约 87%。

Objective 5 虽然数值最低，但本机只有 Docker，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。按 stop rule，不继续堆 Objective 5 本地 metadata。

在 Docker-only 且无真实手机、硬件、现场材料时，最低可行动作是继续 Objective 1 / Objective 4 的硬件传感器基线与 HIL-entry 准备链：让未来真实 2D LiDAR / ToF 材料进入 HIL 前先通过参数化 config precheck，避免工程实现把 sensor count、thresholds、frame IDs、safety policy 写死。

## 4. PR #5 Review 证据

本轮规划直接承接 GitHub PR #5 review：

- P1：default hardware set 与 mandatory sensor baseline 不一致，说明产品硬件边界和工程默认参数不能继续分叉。
- P2：OKR lowest-objective claim 不一致，说明 sprint 选择必须先说明 Objective 5 数值最低但外部证据 blocked 的转向理由。
- P2：mandatory sensor assumptions 缺 `docs/vendor/` source attribution，说明 2D LiDAR / ToF 不能被描述成已采购、已安装、已标定或 HIL-ready。

本轮要把这些 review 风险继续向前推进：不是再查一遍 source，而是定义未来 HIL-entry sensor config 的参数化 contract 和跨端 fail-closed 消费口径。

## 5. 用户价值和产品北极星

用户价值：普通用户和现场支持不需要理解 ROS2、传感器 SKU、frame tree 或安全阈值，也能看到“当前传感器 HIL-entry 配置是否只是准备好被检查，还是已经有真实材料”。工程同学也不能用单一 SKU 默认值绕过采购、安装、标定和 HIL 证据。

产品北极星：把 `rober` 做成普通手机用户可用、现场可诊断、硬件假设可追溯的低成本 ROS2 送垃圾机器人。本轮核心不是证明硬件已经通过，而是防止未来硬件 HIL-entry 前的配置硬编码、证据缺失和手机端误导性成功文案。

## 6. 本轮核心抓手

建立 `trashbot.hardware_sensor_hil_entry_config_precheck.v1` / summary v1：

- PC gate 只验证 future HIL-entry sensor config 的参数化完整性与证据引用。
- Robot diagnostics 只做 metadata-only consumer，缺失或不安全字段必须 fail closed。
- mobile/web 新增只读 phone-safe panel，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。
- Product closeout 只在实现完成后更新 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint 收口文档，不提前宣称 OKR 进展。

## 7. 证据边界

本轮预期边界固定为：

- `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`
- `software_proof` only
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

明确不证明：

- not real WAVE ROVER / UART / HIL
- not real 2D LiDAR / ToF procurement / install / wiring / calibration
- not real phone / browser
- not Objective 5 external proof

## 8. 责任 Owner

- Task A Hardware：Hardware Infra Engineer。
- Task B Robot：Robot Platform Engineer。
- Task C Full-stack：User Touchpoint Full-Stack Engineer。
- Task D Product closeout：Product Manager / OKR Owner。

本轮属于 4 owner epic sprint，文件范围互不重叠，后续实现阶段必须并行派 4 个 worker；主节点只做派发、验收、集成判断和 sprint 留档。

## 9. 风险、阻塞和证据链

- 真实硬件仍 blocked：没有 WAVE ROVER/UART/HIL packet、真实 2D LiDAR / ToF SKU/source/receipt、安装/接线/供电/标定材料。
- Objective 5 external proof 仍 blocked：没有 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- 手机证明仍 blocked：没有真实 iPhone/Android、production app、PWA prompt/user choice。
- 本轮如果实现完成，也只能说明 HIL-entry config precheck contract 可被软件验证；不能把 config readiness 写成 hardware readiness。

