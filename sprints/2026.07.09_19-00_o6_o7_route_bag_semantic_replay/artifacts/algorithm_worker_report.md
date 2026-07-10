# Algorithm Worker Report

- 角色：robot-algorithm-engineer
- sprint：`2026.07.09_19-00_o6_o7_route_bag_semantic_replay`
- 运行时间：2026-07-09 19:13:48 CST
- 证据边界：`software_proof_route_bag_semantic_replay_only`

## 实际改动的文件列表

- `onboard/scripts/field_route_evidence_manifest.py`
  - 完成 `trashbot.route_bag_semantic_replay.v1` 的 CDR 摘要生成链路稳定性修正。
  - `summarize_route_bag_semantic_replay` 已在 `decode` 失败时做 fail-closed 降级，保证结果总是同形闭环。
  - `decode_laserscan_payload` / `decode_image_payload` / `decode_tf_message_payload` 增加 strict 与 permissive 解析器双通道，修正 Image、TF 在测试 payload 中因对齐差异导致的 `cdr_buffer_underrun`。
  - `route_bag_semantic_replay` 继续输出到 manifest 顶层和 `field_motion_evidence_packet.route_bag_semantic_replay`。
- `docs/navigation/field_route_evidence_manifest.md`
  - 补充 `route_bag_semantic_replay` 的输入、白名单语义、失败条件和 manifest 字段清单（与 proof_scope 一并描述）。
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/algorithm_worker_report.md`
  - 本次运行记录。

## 验证命令输出结果

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

输出：37 tests PASS。

```text
Ran 37 tests in 0.169s

OK
```

## 失败定位

- 首轮执行中 `Image` 与 `TFMessage` 的 CDR 解析触发 `cdr_buffer_underrun`，导致 `route_bag_semantic_replay` 进入 `blocked_not_proven`。
- 根因是测试 payload 使用了非严格对齐特征；原始 strict-only 解析器与该 payload 格式不匹配。
- 处理：引入 permissive 回退读路径，在 strict 失败后再尝试无对齐解析，确保语义字段可复现摘要。

## 剩余风险

- 当前仍为白名单、有限统计层，无法从 DB3 推断真实 route execution、robot pose 趋势或 delivery 成功。
- CDR 解析是统计级别，若未来 rosbag payload 与现有 `rosbag2` schema 有偏移（字段顺序/对齐方式差异更大），仍可能出现新的 fail-closed，需要按新 format 补充解码策略。
