# Board Offline Evidence Intake Final

## 收口结论

本轮机器人侧主线完成：现场材料不再必须通过当前开发机 SSH 到 `192.168.1.11:37878` 才能进入证据链。`field_route_evidence_manifest.py --mode local --input <packet_dir>` 已可直接把本地 evidence packet 转成 `trashbot.field_evidence_manifest.v1`，并复用既有 manifest gate。

## OKR 回顾

- 归档 O3 现场 lane：本轮不提升真实路线/送达完成度，只补齐非 SSH 的现场材料导入路径。
- O6：离线 packet 可作为后续 archive/consumer read 的输入材料。
- O7：PC 端 route replay / labeling consumer 可以继续读取同一 manifest schema，不应把 `not_proven` 展示成成功交付。

`tech-plan.md` 的最低优先级判断仍成立：继续强攻 live SSH 会第三次消费同一 blocker；本轮改走离线 intake 是对 O7/O6 的前置推进。

## 验证证据

- `python3 -m py_compile`：通过。
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`：通过，8 tests OK。
- `field_route_evidence_manifest.py --help`：通过，显示 `--input` alias。
- `--mode local --input /tmp/trashbot_field_evidence_fixture`：通过，生成 `trashbot.field_evidence_manifest.v1`，`gate_pass=true` 且 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- `rg -n "trashbot.field_evidence_manifest.v1|delivery_success|safe_to_control|primary_actions_enabled|not_proven|artifact_status|gate_pass" onboard pc-tools sprints/2026.06.09_21-03_board-offline-evidence-intake`：通过，退出码 0。
- `git diff --check`：通过，无输出。

## 剩余风险

- 本轮证据边界是 `software_proof_offline_fixture_only`，不是 HIL、真实 SSH、真实路线采集或真实送达。
- 真实现场材料仍需人工导出后再喂给同一 `--input` 路径。
- 真实 SSH `No route to host` 仍未解决，但不再阻塞本轮 P0。

## 协同判断

- Product：不需要新决策，当前切换 away from repeated SSH blocker 的方向已执行。
- Hardware：不需要，本轮未修改硬件配置、WAVE ROVER、UART 或 launch 参数。
- Autonomy：只读咨询已确认 `--input`/`--artifact-root` 不一致需要处理，本轮已按建议支持 alias。
- Full-Stack：如 PC worker 有并行结果，可继续核对 `trashbot.field_evidence_manifest.v1` 与 `input_manifest` 摘要展示；机器人侧未触碰 `pc-tools/**`。
