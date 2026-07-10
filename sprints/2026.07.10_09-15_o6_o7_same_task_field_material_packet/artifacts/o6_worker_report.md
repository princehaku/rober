# O6 Worker Report

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 实现摘要

- 新增 O6 schema `trashbot.o6.same_task_field_material_packet.v1` 与 proof scope `software_proof_same_task_field_material_packet_only`。
- 新增 same-task field material packet summarizer、placeholder、request 提取与 pre-scan 剥离逻辑。
- 支持从 manifest 顶层、artifact bundle 顶层和 `field_motion_evidence_packet.same_task_field_material_packet` 读取 additive packet。
- 将该 section 接入 field evidence / artifact bundle 写入、archive detail、consumer detail 顶层 alias、`field_evidence_consumer_ingest` / `artifact_bundle_consumer_ingest` 与 `include=same_task_field_material_packet`。
- fail-closed 规则保持 section 级降级：unsafe text、绝对路径、URL/credential query、token、raw/base64、dangerous true 只把当前 packet 降为 `blocked_not_proven`，不让整条 archive 写入 400。
- 返工后按 Algorithm 实际 shape 调整为优先读取 `material_summaries.<material>`，兼容旧 fixture 的 dict-shaped `sample_refs` 与更早的顶层材料字段。
- 返工后接受 `map_yaml` 作为 optional 材料，缺失时只追加 `same_task_field_material_map_yaml_missing_optional` / `map_yaml_material_optional`，不会单独破坏其他材料的 ready 状态。
- 返工后 O6 输出顶层 `sample_refs` 为 basename list，并额外输出 `material_sample_refs` 供 O7 做逐材料展示。

## 验证结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

- 结果：通过

### 2. 单元测试

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

- 结果：`Ran 169 tests in 66.620s`，`OK`

### 3. diff check

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
```

- 结果：通过

## Proof Boundary

- 本轮只证明 `same_task_field_material_packet` 在 O6 local/mock archive/readback 模型中可被安全写入、降级和回读。
- 本轮不证明真实 production cloud、真实 OSS/CDN、真实 route execution、真实 operator confirmation、真实 delivery success、真实机器人控制执行或硬件安全。
- 所有 readback 仍固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`connects_cloud_production=false`。

## 剩余风险

- 如果 Algorithm 后续再次调整 `material_summaries` 字段名、count 口径或 sample refs 内容格式，O6 仍可能按 fail-closed 把该 section 降级，需要联调时继续盯真实 packet。
- 本轮未改 O7；O7 侧 consumer / UI 仍需单独接住 `same_task_field_material_packet` 才能完成端到端展示。
