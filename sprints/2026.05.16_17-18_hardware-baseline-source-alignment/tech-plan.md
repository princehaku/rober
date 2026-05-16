# Sprint 2026.05.16_17-18 Hardware Baseline Source Alignment - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 是否针对最低 Objective：否。
3. 理由：Objective 5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部材料；当前主机只有 Docker，继续本地 metadata 不能形成有效 O5 completion。下一层最低可推进 Objective 是 Objective 1（约 73%），且 PR #5 review 的 P1/P2 硬件基线/source 引用问题正是 O1 可推进缺口。

## 1. 技术方案

新增 `hardware_baseline_source_alignment` 一条软件证明链：

1. Hardware PC gate 读取 `docs/product/production_hardware_boundary.md` 与 `docs/vendor/VENDOR_INDEX.md`，检查默认硬件集、目标传感器基线、vendor coverage/source boundary 和 pending/not_proven 语义是否一致。
2. Robot diagnostics 只读消费 artifact / summary，生成 metadata-only diagnostics summary。
3. mobile/web 只读展示该 summary，并提供 whitelist-only copy/export。

## 2. 文件范围

Task A - Hardware Infra Engineer：

- `pc-tools/evidence/hardware_baseline_source_alignment_gate.py`
- `pc-tools/evidence/test_hardware_baseline_source_alignment_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

Task B - Robot Platform Engineer：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task C - User Touchpoint Full-Stack Engineer：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Task D - Product Manager / OKR Owner：

- `sprints/2026.05.16_17-18_hardware-baseline-source-alignment/tech-done.md`
- `sprints/2026.05.16_17-18_hardware-baseline-source-alignment/side2side_check.md`
- `sprints/2026.05.16_17-18_hardware-baseline-source-alignment/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 接口契约

PC artifact:

- `schema=trashbot.hardware_baseline_source_alignment.v1`
- `summary_schema=trashbot.hardware_baseline_source_alignment_summary.v1`
- `source=software_proof`
- `evidence_boundary=software_proof_docker_hardware_baseline_source_alignment_gate`
- `alignment_status` 支持：
  - `hardware_baseline_source_alignment_not_proven`
  - `blocked_missing_hardware_boundary`
  - `blocked_missing_vendor_index`
  - `blocked_incomplete_hardware_source_alignment`
  - `blocked_success_or_control_claim`
- 必须输出 `default_hardware_set_summary`、`target_sensor_baseline_summary`、`vendor_source_boundary`、`missing_alignment_items`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Robot/mobile summary 只允许 phone-safe metadata，不得复制 raw vendor docs、完整 artifact、raw JSON、本机路径、serial/UART path、token/credential、成功或控制放行文案。

## 4. 验收命令

Task A：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/hardware_baseline_source_alignment_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_hardware_baseline_source_alignment_gate.py
python3 pc-tools/evidence/hardware_baseline_source_alignment_gate.py --help
rg -n "hardware_baseline_source_alignment|software_proof_docker_hardware_baseline_source_alignment_gate|docs/vendor/VENDOR_INDEX.md|hardware_material_pending|not_proven" pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_baseline_source_alignment_gate.py pc-tools/evidence/test_hardware_baseline_source_alignment_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

Task B：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_baseline_source_alignment|software_proof_docker_hardware_baseline_source_alignment_gate|metadata_only|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_baseline_source_alignment|硬件基线来源对齐|software_proof_docker_hardware_baseline_source_alignment_gate|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task D：

```bash
rg -n "hardware_baseline_source_alignment|software_proof_docker_hardware_baseline_source_alignment_gate|Objective 1|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_17-18_hardware-baseline-source-alignment OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_17-18_hardware-baseline-source-alignment OKR.md docs/process/okr_progress_log.md
```

## 5. 风险边界

- 本轮最多证明 source-alignment software proof，不证明真实传感器、采购、接线、标定、HIL、Nav2/fixed-route、手机设备或 delivery success。
- 如果 worker 发现 `production_hardware_boundary.md` 已经部分修复 PR #5 review，仍要把该一致性变成可重复 gate 和下游 metadata contract，而不是只做文档总结。
