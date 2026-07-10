# O6/O7 Same-Task Route Execution Material Packet Tech Done

## Sprint 声明

- `sprint_type: epic`
- Product closeout 时间：2026-07-10 11:53 CST
- Sprint 路径：`sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/`
- 目标 Objective：O6 云端核心后端、O7 PC 端运营调试平台。
- 证据边界：`software_proof_same_task_route_execution_material_packet_only`。

## 实际改动

### Algorithm producer

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `trashbot.same_task_route_execution_material_packet.v1`。
  - 从同一 `task_id` 的 field material packet、route execution readiness/closure、Nav2、delivery result、pose progress、route bag replay 和 replay JSONL 中生成安全摘要。
  - 输出 manifest 顶层 `same_task_route_execution_material_packet`，并嵌入 `field_motion_evidence_packet.same_task_route_execution_material_packet`。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 增加 ready、缺 route execution material blocked、unsafe linked summary fail-closed 三类覆盖。
- `docs/navigation/field_route_evidence_manifest.md`
  - 同步新增 schema、字段、ready/blocked 语义和安全边界。

### O6 archive/readback

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `trashbot.o6.same_task_route_execution_material_packet.v1` readback schema。
  - 支持 field evidence、artifact bundle、archive detail、consumer detail 顶层 alias 与 `include=same_task_route_execution_material_packet` 回读。
  - 对 schema mismatch、proof/evidence boundary mismatch、task mismatch、unsafe text、dangerous true、raw/base64、绝对路径、credential-like URL、token/secret/connection string、traceback/response body 做 section-local fail-closed。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加同 task route execution packet 回读、include、fail-closed 和 negative fixture 覆盖。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 同步 O6 packet 合同和只读安全边界。

### O7 consumer/UI

- `pc-tools/workstation/src/shared/contracts.ts`
  - 增加 O7 same-task route execution material packet 类型。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 默认 include 新 packet，并从 O6 top-level、field evidence、field motion、artifact bundle、consumer ingest 和 readiness 中读取。
  - 新增 schema/task/proof/unsafe/dangerous fail-closed，且 readiness 只信 O6 顶层 packet status。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 新增独立 `Same task route execution material packet` 展示区。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 增加 UI、adapter、default include、packet summary 和 fail-closed 覆盖。
- `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`
  - 同步 O7 默认 include、展示语义和安全边界。

### Product closeout

- `tech-done.md`、`side2side_check.md`、`final.md`、`artifacts/product_worker_report.md`
  - 记录 Product 验收、OKR 判断和剩余风险。
- `OKR.md`、`docs/process/okr_progress_log.md`
  - 更新当前状态、4.1 快照、近期记录和详细进度日志。

## 验证证据

| Owner | 命令 | 结果 |
| --- | --- | --- |
| Algorithm | `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` | 通过，无输出 |
| Algorithm | `python3 -m unittest onboard.tests.test_field_route_evidence_manifest` | `Ran 65 tests in 0.453s` / `OK` |
| Algorithm | scoped `git diff --check` | 通过，无输出 |
| O6 | `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` | 通过，无输出 |
| O6 | `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` | `Ran 171 tests in 68.334s` / `OK` |
| O7 | `cd pc-tools/workstation && npm run test && npm run build && npm run lint` | `Tests 486 passed (486)`，build 通过，lint exit code 0 |
| O7 | scoped `git diff --check` | 通过，无输出 |

## 失败定位与修复

- Algorithm：最终验收没有失败；首轮 `py_compile` 和单测即通过。
- O6：首轮完整 unittest 失败 1 个 negative fixture 断言。根因是 fixture 改了 artifact bundle `task_id`，但未同步既有 `same_task_field_material_packet.task_id`，先触发旧合同的 task mismatch fail-closed。已同步 fixture 后复跑通过。
- O7：第一轮 `npm run test` 暴露 4 个 catalog fixture/断言问题，包括 default include 未包含新 packet、legacy fixture 缺同 task packet、mission gate fail-closed fixture 先命中 packet mismatch，以及 artifact readiness source 断言仍按旧 nested bundle source。已修复 fixture 和断言后复验通过。

## 偏差

- 本轮达到 PRD/tech-plan 的 P0 目标：Algorithm -> O6 -> O7 三层围绕同一 `task_id` 消费 `same_task_route_execution_material_packet`，并保留 fail-closed 与 fixed false flags。
- 本轮没有新增真实 production cloud、生产 DB/queue、真实 live Nav2 route execution、真实 robot motion、delivery record、operator confirmation、delivery success 或 hardware safety/HIL 材料。
- O7 report 仍提示：如果 O6/Algorithm 后续调整 packet 字段名或 material alias，需要再跑一次同 task 联调 smoke。当前 worker report 所列字段已经完成本轮合同对齐。

## 剩余风险

- `route_execution_material_consumed=true` 只表示软件安全摘要可被链路消费，不等于 route execution success。
- `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false` 必须继续固定。
- 本轮不证明真实 production cloud、production DB/queue、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或 hardware safety。
- 下一轮若继续 O6/O7，必须接 live route execution、delivery record、operator confirmation 或 production cloud readback；否则只能算回归守护。
