# O6/O7 PC Live Nav2 Execution Material Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective：O5，约 `~85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对理由：O5 上一轮 `cloud_production_cutover_readiness_packet` 已固定 `okr_credit_allowed=false`，当前环境缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser evidence。继续 O5 support-only surface 不应提升主 OKR。O1 最近两轮也已连续指向 current live HIL 同一 blocker，所以本轮转向可消费不同 live material delta 的 O6/O7。

## 技术方案

新增 additive section：`pc_live_nav2_execution_material`。

Producer 输入为安全 JSON material，字段来自 `sprints/2026.07.03_20-46_pc_nav2_o11_tail_wasd_back_alias/tech-done.md` 的 live verification record。Algorithm owner 需在本 sprint `artifacts/` 下创建一个短 JSON fixture/source material，用于测试和 CLI smoke；该文件必须只包含短安全字段，不包含 URL、path、token、raw log、traceback 或 base64。

目标 status：

- ready: `pc_live_nav2_execution_material_ready_not_delivery_proof`
- blocked: `blocked_not_proven`

proof scope：

- `software_proof_pc_live_nav2_execution_material_only`

## 任务分工

### Algorithm owner

文件范围：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/algorithm_worker_report.md`
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/pc_live_nav2_execution_material_source.json`

实现要求：

- 新增 CLI 参数 `--pc-live-nav2-execution-material-json`。
- 生成 manifest 顶层和 `field_motion_evidence_packet.pc_live_nav2_execution_material`。
- 对 dangerous true 和 unsafe text fail-closed；尤其不能输出 `delivery_success=true`、`safe_to_control=true`、`primary_actions_enabled=true`、`route_execution_success=true`、`hil_pass=true`。
- 源 material 里的 `robot_control_executed` 只能作为 source fact 摘要，不得打开 manifest 顶层控制字段。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

### Robot Software / O6 owner

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o6_worker_report.md`

实现要求：

- O6 支持 `pc_live_nav2_execution_material` archive/readback/include。
- 输出 schema `trashbot.o6.pc_live_nav2_execution_material.v1`。
- 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=pc_live_nav2_execution_material`。
- 缺字段、bad schema/proof scope、dangerous true、unsafe text 时只把该 section blocked，不污染其它 section。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

### Full-stack / O7 owner

文件范围：

- `pc-tools/workstation/src/`
- `pc-tools/workstation/test/`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/artifacts/o7_worker_report.md`

实现要求：

- O7 consumer adapter 默认 include/consume `pc_live_nav2_execution_material`。
- UI 展示 ready status、source sprint、goal accepted、UART/base command/IMU facts、wheel L/R false、remaining evidence。
- 所有控制和成功字段保持 false，不新增任何执行按钮。

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- pc-tools/workstation docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material
```

## 集成验收

- 三个 worker report 均存在。
- 关键字段能从 Algorithm -> O6 -> O7 保持一致。
- `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`route_execution_success=false`、`hil_pass=false` 全链路不变。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 最终只在 Product closeout 阶段更新。
