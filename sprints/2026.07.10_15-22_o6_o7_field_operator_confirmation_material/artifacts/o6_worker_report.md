# O6 Worker Report

## 基本信息

- 角色：robot-software-engineer
- 时间：2026-07-10 15:41:39 +0800
- 范围：O6 archive/readback/include 新增 `field_operator_confirmation_material`
- 证据边界：`software_proof_field_operator_confirmation_material_only`

## 实际改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/o6_worker_report.md`

## 实际实现内容

- 新增 `trashbot.o6.field_operator_confirmation_material.v1` O6 schema 常量、proof scope 常量和 `include=field_operator_confirmation_material` 白名单。
- 新增 section-local sanitizer / summary / placeholder / consumer include handler，支持从 field evidence payload/container 顶层、`field_motion_evidence_packet`、artifact bundle、readiness 和 consumer detail 摘要中抽取 `field_operator_confirmation_material`。
- 输入 schema 兼容 `trashbot.field_operator_confirmation_material.v1` 和 `trashbot.o6.field_operator_confirmation_material.v1`，回读 schema 固定为 `trashbot.o6.field_operator_confirmation_material.v1`。
- ready status 统一输出 `field_operator_confirmation_material_ready_not_delivery_proof`，proof scope 固定为 `software_proof_field_operator_confirmation_material_only`。
- 对缺字段、task mismatch、proof scope mismatch、危险 true、unsafe raw/path/token/url/base64/traceback、缺 operator material identity 等情况做 section-local `blocked_not_proven`，不阻断其它 additive section。
- archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest` 和 consumer detail 顶层 alias 均已回读新 section。
- 新增 field evidence / artifact bundle ready path 回归，以及 missing、bad schema、bad proof scope、task mismatch、missing required field、unsafe text、dangerous true 回归。
- 同步更新 O6 Cloud Archive API 文档，明确 schema、proof boundary、字段、include 和 fail-closed 行为。

## 验证命令和结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

结果：

```text
Ran 177 tests in 75.477s

OK
```

## 失败定位

- 本轮 `py_compile` 和完整 relay unittest 均通过，未留下需要修复的失败。

## 剩余风险

- 本轮只证明 O6 local/mock archive/readback 能安全消费 operator confirmation material，不证明 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery success、真实 operator acceptance、HIL 或 hardware safety。
- O7 默认 include/UI 消费仍需 full-stack owner 完成并验证。

## 协同需求

- 需要 Full-Stack/O7 owner 对接 `trashbot.o6.field_operator_confirmation_material.v1` 的默认 include 和只读展示。
- 若 Algorithm 后续调整 material summary 字段名，Robot Software 需要复核 O6 allowlist 是否仍兼容。
