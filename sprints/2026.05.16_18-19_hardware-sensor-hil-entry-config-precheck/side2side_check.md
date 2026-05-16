# Sprint 2026.05.16_18-19 Hardware Sensor HIL-entry Config Precheck - Side-by-side Check

sprint_type: epic

## 1. 核对对象

本轮 side-by-side check 对照 GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` review 证据，确认 review 风险是否被转成可执行 contract，而不是只停留在 PRD 或说明文字。

## 2. PR #5 Review 证据转 contract 核对

| PR #5 review 证据 | 本轮可执行 contract | 结果 |
| --- | --- | --- |
| default hardware set vs target baseline 口径不一致 | `hardware_sensor_hil_entry_config_precheck` 继承上轮 source-alignment 边界，把 future HIL-entry sensor config 的 sensor count、thresholds、frame IDs、safety policy、evidence refs 显式参数化；不把 product target 写成 installed/proven hardware。 | 已转成 PC gate、Robot metadata-only consumer、mobile read-only panel。 |
| 防最低 OKR 口径漂移 | `tech-plan.md` 与 `final.md` 均回顾 Objective 5 数值最低，但真实外部 cloud/4G/OSS/CDN/DB/queue 材料 blocked；本轮只转向 O1/O4 的硬件 config software proof。 | 已写入 sprint 留档，Objective 5 不上调。 |
| `docs/vendor/` source attribution | Task A 已读 `docs/vendor/VENDOR_INDEX.md`、WAVE ROVER `config.yaml`、`base_ctrl.py`、`json_cmd.h`；文档明确 vendor source 只能证明 Orange Pi / WAVE ROVER / UART JSON / firmware/vendor app 边界，不能证明真实 2D LiDAR / ToF。 | 已落到 `docs/product/production_hardware_boundary.md` 与 Product closeout 边界。 |
| 参数化 config precheck | Contract 要求 sensor count、thresholds、frame IDs、safety policy 和 evidence refs 参数化；缺失、unsupported、unsafe、success claim、弱 boundary fail closed。 | 已由 PC gate tests、Robot diagnostics tests、mobile tests 覆盖。 |

## 3. 证据边界核对

- Contract：`trashbot.hardware_sensor_hil_entry_config_precheck.v1` / `trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1`。
- Evidence boundary：`software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`。
- 状态固定：`software_proof` only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start / Confirm Dropoff / Cancel gating：未改变。
- Copy/export：whitelist-only；无 `safe_copy` 时 blocked copy unavailable。

## 4. 不可声明内容核对

本轮不得声明以下结果，当前文档和 closeout 均按此收口：

- 真实 WAVE ROVER/UART/HIL 通过。
- 真实 2D LiDAR / ToF 已采购、安装、接线、供电、标定或 HIL-entry。
- 真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion 或 delivery success。
- 真实手机/browser、production app、PWA prompt/user choice。
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 5. 结论

PR #5 review 的四类可执行风险已经被本轮 contract 串起来：default hardware vs target baseline 不再只靠文档说明，最低 OKR 转向理由有 closeout 复核，vendor/source attribution 明确绑定本地资料边界，future HIL-entry config 进入参数化 precheck。验收结论仍是 `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`，不是 HIL 或真实硬件通过。
