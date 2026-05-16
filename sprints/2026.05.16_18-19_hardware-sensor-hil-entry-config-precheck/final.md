# Sprint 2026.05.16_18-19 Hardware Sensor HIL-entry Config Precheck - Final

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：普通用户和现场支持能在手机端看到“传感器 HIL 入口配置预检”只读状态，知道当前只是 software proof 的配置预检，不会误以为真实 2D LiDAR / ToF、真实 HIL 或真实送达已经通过。工程同学也必须在 future HIL-entry sensor config 中显式给出 sensor count、thresholds、frame IDs、safety policy 和 evidence refs，不能把单一 SKU 或单一安装假设写死。

产品北极星：`rober` 继续朝普通手机用户可用、现场可诊断、硬件假设可追溯的低成本 ROS2 自主垃圾投递机器人推进。本轮价值是把 PR #5 review 暴露的硬件基线和 HIL-entry 入口风险转成可机器验收的 fail-closed contract。

## 2. OKR 映射与 KR 更新

- Objective 1：从约 74% 保守上调到约 75%。理由是 HIL-entry sensor config precheck 已覆盖参数化配置、证据引用、vendor/source boundary 和 fail-closed 策略，能防止未经证实的 sensor count、thresholds、frame IDs、safety policy 进入未来硬件/HIL 计划。
- Objective 4：从约 87% 保守上调到约 88%。理由是 mobile/web 新增 phone-safe 只读 panel，能向普通用户和现场支持解释 HIL-entry config precheck 的缺口与下一步材料，同时保持 Start / Confirm Dropoff / Cancel gating 不变。
- Objective 2 / Objective 3：保持约 79%。本轮没有真实 route/elevator field pass、真实 Nav2/fixed-route runtime log、dropoff/cancel completion、task delivery result 或同一 `evidence_ref` 的上车实机复账。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部 O5 材料；不能上调。

KR 拆解更新：

- O1 KR hardware-source/config discipline：future HIL-entry sensor config 必须通过 `trashbot.hardware_sensor_hil_entry_config_precheck.v1` 的参数化 precheck。
- O4 KR phone-safe diagnostics：手机端只读展示 precheck status、safe evidence ref、sensor count summary、threshold summary、frame IDs summary、safety policy summary、missing config/material summary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- O5 KR external proof：仍等待真实外部材料；本轮不替代 O5。

## 3. 本轮核心抓手和完成结果

核心抓手：`hardware_sensor_hil_entry_config_precheck` contract。

已完成：

- Task A Hardware：PC gate + tests + hardware boundary docs。
- Task B Robot：diagnostics metadata-only consumer + tests + ROS contract docs。
- Task C Full-stack：mobile/web 只读 panel + tests + mobile product flow docs。
- Task D Product：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` closeout。

## 4. 优先级和验收口径

P0 已完成：

- Contract 名称、schema、evidence boundary、fail-closed status 固化。
- PC gate 拒绝硬编码单一 SKU / 单一 sensor count / 缺 thresholds / 缺 frame IDs / 缺 safety policy / 缺 evidence refs 的风险路径。
- Robot diagnostics 和 mobile/web 不改变 primary actions。

P1 已完成：

- 同步 `pc-tools/README.md`、`docs/product/production_hardware_boundary.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- Product closeout 说明 Objective 5 stop rule 与 Objective 1 / Objective 4 的 software-proof 边界。

验收通过只代表 `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 对应责任 Engineer

- Task A Hardware：Hardware Infra Engineer。
- Task B Robot：Robot Platform Engineer。
- Task C Full-stack：User Touchpoint Full-Stack Engineer。
- Task D Product closeout：Product Manager / OKR Owner。

## 6. OKR 最低优先级核对

本轮 tech-plan 记录的最低 Objective 是 Objective 5，约 66%。Final 回顾后，转向仍成立：

- Objective 5 仍是数值最低。
- 本机仍只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他外部材料。
- 本轮没有新增 O5 external proof，因此 Objective 5 保持约 66%。
- 转向 Objective 1 / Objective 4 仍成立，因为 PR #5 review 暴露的 default hardware set vs target baseline、vendor/source attribution、最低 OKR 口径漂移和参数化 config precheck 风险可以在 Docker-only 环境中形成可执行 software proof。

## 7. 验证结果

A/B/C worker 结果：

```text
Task A Hardware:
py_compile pass
unittest Ran 9 tests OK
CLI help pass
required rg pass
scoped diff check pass

Task B Robot:
py_compile pass
diagnostics unittest Ran 108 tests in 0.114s OK
required rg pass
scoped diff check pass

Task C Full-stack:
mobile unittest Ran 10 tests in 0.019s OK
node --check pass
required rg pass
scoped diff check pass
```

Task D Product closeout 最终验证：

```text
rg -n "hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false|PR #5" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck
pass; matched OKR.md, docs/process/okr_progress_log.md, pre_start.md, prd.md, tech-plan.md, tech-done.md, side2side_check.md, and final.md

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/tech-done.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/side2side_check.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/final.md
pass; no output
```

## 8. 风险、阻塞和证据链

剩余风险：

- 不是真实 WAVE ROVER/UART/HIL。
- 不是真实 2D LiDAR / ToF 采购、安装、接线、供电、标定或 HIL-entry。
- 不是真实手机/browser、production app 或 PWA prompt/user choice。
- 不是真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion、delivery success。
- 不是真实 Objective 5 external proof。

需要补齐的证据链：

- 2D LiDAR / ToF SKU/source/receipt/procurement materials。
- 安装、接线、供电、电气安全材料。
- 标定结果、frame tree 校验与真实 HIL-entry logs。
- 真实 iPhone/Android device behavior、production app、PWA prompt/user choice。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 9. 收口结论

本轮完成 hardware sensor HIL-entry config precheck 的 software-proof 闭环，可以保守记录 Objective 1 与 Objective 4 小幅进展。所有文档必须继续保持 `software_proof` only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不能把本轮结果写成真实硬件、真实手机/browser、真实 HIL、真实送达或 Objective 5 external proof。
