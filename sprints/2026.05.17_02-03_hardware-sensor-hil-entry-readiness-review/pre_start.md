# Sprint 2026.05.17_02-03 Hardware Sensor HIL-entry Readiness Review - Pre Start

sprint_type: epic

## 1. 启动背景

本轮启动于 2026-05-17 02:02 Asia/Shanghai。用户要求“根据近期 PR 和评审，建议下一步应深入的 OKR”，并明确本机没有真实硬件、只有 Docker，同时要求用 team 继续把功能往前推、测试只做围栏、优先推进低完成度 OKR。

## 2. 证据输入

- `OKR.md` 4.1 当前快照：Objective 5 约 66%，数值最低；Objective 1 约 75%，是 O5 外部证据不可用后最低的可行动作区。
- PR #5 review P1：`docs/product/production_hardware_boundary.md` 曾出现 Default Hardware Set 与 `monocular + 2D LiDAR + ToF` mandatory baseline 的冲突，要求默认硬件与目标传感器基线一致且可追溯。
- PR #5 review P2：新增 mandatory sensor assumptions 必须引用 `docs/vendor/` 来源，不能把 2D LiDAR / ToF 的 product target 写成已采购、已安装或已 HIL 的事实。
- 最近 sprint `2026.05.17_01-02_route-task-field-retest-operator-drill/final.md`：O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；继续本地 O5 wrapper 会重复消费 Docker-only blocker。
- 最近硬件 sprint `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/final.md`：已有 HIL-entry config precheck，但还没有把 receipt intake 与 config precheck 合成“是否可进入 HIL-entry 材料评审”的统一 readiness decision。

## 3. 本轮目标

建立 `hardware_sensor_hil_entry_readiness_review` gate：在 Docker-only software proof 边界内，把 2D LiDAR / ToF 的 receipt-intake summary 与 HIL-entry config-precheck summary 合成一个 fail-closed readiness review artifact / summary，并让 Robot diagnostics 与 mobile/web 只读消费。

本轮不证明真实 WAVE ROVER、真实串口、真实 2D LiDAR / ToF、真实 HIL、真实 Nav2/fixed-route、真实手机或 O5 external proof。

## 4. Owner 和并行策略

- Hardware Infra Engineer：新增 PC readiness review gate，读取 `docs/vendor/VENDOR_INDEX.md` 和现有 receipt/precheck summaries，输出 fail-closed artifact / summary。
- Robot Platform Engineer：新增 diagnostics metadata-only consumer，确保 unsupported/missing/success claim/weak boundary fail closed。
- User Touchpoint Full-Stack Engineer：新增 mobile/web 只读 panel，展示 readiness decision、missing materials、next required evidence 和边界。
- Product Manager / OKR Owner：收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

文件范围互不重叠，默认 3 个工程子 agent 并行启动；Product closeout 在工程结果返回后执行。

## 5. Blocker 扫描

最近两轮 route-task sprint 的主要 blocker 是真实现场 route/elevator 材料缺失，不是本轮硬件 HIL-entry readiness review 的同一根因。Objective 5 外部证据仍被 Docker-only 环境锁定，本轮按 stop rule 切到 Objective 1 / Objective 4。
