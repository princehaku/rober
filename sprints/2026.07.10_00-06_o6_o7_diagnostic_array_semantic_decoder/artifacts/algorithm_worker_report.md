# Algorithm Worker Report - DiagnosticArray Semantic Decoder

run_time: 2026-07-10T00:14:51+0800
owner: robot-algorithm-engineer
sprint: 2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder

## 自主能力目标和本轮抓手

目标是把 route bag full semantic decode matrix 中的 `diagnostic_msgs/msg/DiagnosticArray` 从 unsupported 推进为 decoded，同时保持 O6/O7 可消费摘要的 fail-closed 边界。本轮抓手是新增有限 CDR decoder，并用 fixture DB3 验证 semantic replay 与 full matrix 的安全输出。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `diagnostic_msgs/msg/DiagnosticArray` 到 `route_bag_semantic_replay` 白名单。
  - 新增 `decode_diagnostic_array_payload` 到 full semantic decode matrix decoder map。
  - 新增 `diagnostic_array_summary` 输出字段。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 DiagnosticArray CDR fixture builder。
  - 扩展 semantic replay 与 full semantic decode matrix 测试，覆盖 DiagnosticArray decoded、安全字段和敏感文本不回显。
- `docs/navigation/field_route_evidence_manifest.md`
  - 同步记录 DiagnosticArray 支持范围、安全摘要字段和 decoder 白名单。
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/algorithm_worker_report.md`
  - 本报告。

接口影响：`route_bag_semantic_replay` 新增 `diagnostic_array_summary`，`semantic_topic_types` 可包含 `diagnostic_msgs/msg/DiagnosticArray`；`route_bag_full_semantic_decode_matrix.topic_type_matrix[]` 中对应 item 现在可输出 `status=decoded`、`decoder_name=decode_diagnostic_array_payload`。所有 safety flags 继续固定为 false。

## 实现内容

- DiagnosticArray decoder 只读取 Header 后的 status array。
- 输出字段限定为 `status_count`、`highest_level`、`level_distribution`、短 `status_name_samples`、短 `hardware_id_samples`、`key_value_pair_count`。
- `message`、key、value 只做 CDR offset 跳过，不写入 manifest。
- status name / hardware_id 样本只允许短安全标识符；路径、URL、token、base64、raw、traceback、credential 等文本会被丢弃。
- CDR 字符串和数组长度增加上限保护，避免异常 payload 通过超大长度拖垮本地解析。

## 测试、dry-run 或上车验证结果

```text
$ python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
exit code: 0
```

```text
$ python3 -m unittest onboard.tests.test_field_route_evidence_manifest
................................................
----------------------------------------------------------------------
Ran 48 tests in 0.236s

OK
```

```text
$ git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/algorithm_worker_report.md
exit code: 0
```

初次单测失败定位：DiagnosticArray fixture 的 CDR string 后缺少 4 字节对齐，导致 `status_count` 被读成 0，full matrix 未把 DiagnosticArray 计为 decoded。已修正 fixture 对齐后重跑通过。

## 数据、样本或调试输出变化

- semantic replay fixture 中 `/diagnostics` 的 `diagnostic_msgs/msg/DiagnosticArray` 进入 `semantic_topic_types`。
- `diagnostic_array_summary` fixture 输出：
  - `sample_count=1`
  - `status_count=2`
  - `highest_level=2`
  - `level_distribution={"0": 1, "2": 1}`
  - `status_name_samples=["Base OK", "Lidar Warn"]`
  - `hardware_id_samples=["base_board", "lidar_front"]`
  - `key_value_pair_count=3`
- full matrix fixture 中 `/diagnostics` item 输出 `status=decoded`、`decoder_name=decode_diagnostic_array_payload`。
- 测试明确断言 `token-secret`、`voltage_raw`、`Traceback`、`robot:secret`、`SECRET_DIAGNOSTIC_VALUE`、`secret_key` 不出现在 evidence JSON 中。

## 剩余风险和下一步能力建设建议

- 本轮是 local/mock DB3 fixture 软件证明，不证明真实 route bag 已包含 DiagnosticArray，也不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion 或 delivery success。
- DiagnosticArray 只做安全摘要，不保留诊断 message/key/value 原文；后续如需要定位具体硬件故障，应在受控私有日志链路中查看原始 rosbag，而不是通过 O6/O7 manifest 展示。
- 下一步建议由 O6/O7 owner 接入 archive/readback/UI fixture，确认 `diagnostic_array_summary` 和 matrix decoded item 在 consumer detail 中保持同样的 summary-only 边界。
