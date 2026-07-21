# Final：O1 轮速反馈根因诊断

## 收口结论

- `PRODUCT_CLOSEOUT=ACCEPT_SUPPORTING_DIAGNOSTIC_IMPLEMENTATION_READONLY_RUNTIME_INVENTORY_FLAT`
- `status=closed_implemented_validated_supporting_only`
- `sprint_path=sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/`
- `proof_boundary=offline_vendor_v8_diagnostic_plus_single_remote_readonly_inventory_supporting_only`
- `primary_classification=encoder_update_path_not_observed`
- `primary_classification_status=highest_priority_unconfirmed`

旧 `INTEGRATION_CLOSEOUT=BLOCKED_SUBAGENT_RUNTIME_BEFORE_IMPLEMENTATION` / planning-only closeout 已被同一 sprint 后续 Hardware
business-worker 的实现、验证和只读 runtime inventory **supersede**。`pre_start.md` 的 runtime-blocked 状态只记录当时调度事实，
不能覆盖最终 `tech-done.md`、代码、测试、3 个 artifact 与硬件文档证据。

## 用户价值、实际改动与验证

用户价值/产品北极星是可信、安全、可解释的真实底盘控制与反馈闭环。本轮没有再运动猜测，而是新增 fail-closed 离线 CLI、
`12` 个 hostile/normal tests、3 个结构化 artifacts 和硬件诊断文档，并完成一次严格只读 SSH inventory。诊断重算 v8 冻结证据：
nonzero `T=11` 已发送，同窗 3 个 `T=1001` pair 仍为 `0/0`，parser 与冻结 vendor frame 一致；因此首要候选收窄为
`encoder_update_path_not_observed`，但状态明确是 `highest_priority_unconfirmed`，不等于确认 encoder 损坏。

Hardware 留档验证为 py_compile exit `0`、`Ran 12 tests in 0.055s / OK`、真实 CLI exit `0`、safety assertions PASS、三个 JSON
parse PASS、中文技术注释 `20.40%`、scoped diff PASS。Product 不重跑 Engineer tests、SSH 或 control，只做离线文档/artifact
验收：三个 artifact 均通过 `python3 -m json.tool`；结构断言确认 diagnostic schema/status/input、candidate 边界、唯一下一动作、
inventory schema/allowlist/逐条 exit 与所有安全 false/零计数一致。

首次 Hardware 静态自检在测试前发现 vendor define 空匹配可能访问 `matches[0]`，已改为先验证 `len(matches) == 1`，随后
hostile tests 与全量 12 tests 一次通过。Product 额外只读 `jq` 摘要首条表达式因可选访问语法错误未编译；修正为显式
candidate filter 后 exit `0`，不涉及 artifact 或产品文件修改，也不改变验收结果。
Product 首轮 `rg` 文档锚点检查还发现 `side2side_check.md` 缺显式 sprint path、proof boundary、candidate id 与安全字段，
`final.md` 缺显式 sprint path，`OKR.md` 缺两个 runtime candidate id；已仅在四个 Product 文件范围内补齐，复验四文件全部 PASS。

## 当前只读 runtime 事实与安全计数

inventory schema=`trashbot.wave_rover.readonly_runtime_inventory.v1`，SSH session exit `0`；allowlist 和实际五类命令均为
`systemctl_show/systemctl_cat/ps/ss/sha256sum`，逐条 exit `0`。bridge service 为 active/running，上位机 unit 配置为
`command_mode=pwm`、`bridge_main_type=1`、`module_type=0`、`/dev/ttyS5@115200`，并冻结五个 deployed file hash。

`bridge_main_type=1` 只是上位机配置，不是 ESP32 runtime `mainType` 证明；deployed ESP32 firmware build/hash 未由只读接口暴露，
故 `runtime_main_type_not_observed`、`runtime_firmware_identity_not_observed` 保持成立。本轮
motion/control/stop/nonzero/service mutation/UART write/firmware mutation=`0/0/0/0/0/0/0`，HTTP 与 ROS 命令也为 `0`；v8
保持 `consumed_no_retry`，没有 reuse/retry，用户运动授权未被本 sprint 消费。

## OKR、KR 与方向判断

- O1 保持约 `95%`：接受 `current_run_artifact_delta=true` 的 current-run diagnostic implementation + current read-only runtime
  inventory supporting delta；它不构成 HIL、safe-to-control、mission attempt、route 或 delivery credit。
- O5 保持约 `85%`，production provider/runtime blocker `2/2` 继续暂停。
- O6/O7 各保持约 `93%`，corrected Phase0 lane `2/2` 继续暂停，禁止第三轮 Phase0/preflight/wrapper。
- KR `不归档`，当前推进区不移动，已完成 KR 历史区无新增项。
- `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`、`okr_credit=false`；
  `mission_attempt=false`、`hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、
  `delivery_success=false`、`mission_objective_0_satisfied=false`。

Product 方向为“继续 O1，但切到独占维护证据链”，不是继续 motion/readback，也不是新开 review/handoff/status surface。

## 剩余风险与唯一下一动作

仍未证明 deployed ESP32 firmware 与本地 V0.9 source 一致、runtime `mainType`、raw encoder A/B counter delta、encoder
wiring/signal、byte-for-byte raw UART timing、nonzero wheel feedback、HIL、安全准入、路线执行或送达。

唯一下一动作=`maintenance_freeze_runtime_identity_then_observe_raw_encoder_counters`：取得独占 service/UART/firmware 维护授权后，
先冻结 deployed ESP32 firmware identity 与 runtime `mainType`，再增加或读取 raw encoder A/B counter delta；在 counter path 可观测
前不批准新的 motion retry。任何 stop/restart/kill service、UART claim、T=900 或 firmware instrumentation/flash 必须由 CEO/现场
owner 另行明确批准。

## 完成前反思

Product 只修改 `side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`；没有修改 Engineer 代码、测试、
artifacts、硬件文档、`pre_start.md`、`prd.md`、`tech-plan.md` 或 `tech-done.md`。实现证据与 artifact 无冲突，Epic 六文档现已按
最终事实收口；剩余项需要新的独占维护授权，不得用本 sprint 继续消费。

## 收口时间

`2026-07-21 13:11:31 CST (+0800)`
