# Sprint 2026.05.11_22-23 HIL Evidence Packet Gate - Final

## 收口结论

- 时间：2026-05-11 22:15 Asia/Shanghai
- Owner：`hardware-engineer`
- 结论：Docker-only HIL evidence packet gate ready；真实 `hil_pass` pending。
- OKR 影响：O1 证据链更严格，但未新增真实硬件通过证据，不提升 O1 完成度。

## 已交付

- 新增 `scripts/hil_evidence_packet_gate.py`，用于验证 evidence run 目录。
- 更新 HIL 证据文档、runbook、bringup checklist，把 gate 作为真实 evidence 升级前置条件。
- 完成 blocked fixture 与 synthetic valid fixture 验证。

## 关键验证

- `python3 scripts/hil_evidence_packet_gate.py --help`：exit 0。
- `python3 -m py_compile scripts/hil_evidence_packet_gate.py`：exit 0。
- `python3 scripts/hardware_smoke_wave_rover.py --status`：exit 0，`source=software_proof`，`blocked_reason=no_serial_candidates_found`。
- `python3 scripts/hil_evidence_packet_gate.py --packet-dir /tmp/rober_hil_gate_blocked`：exit 1，`status=blocked`。
- `python3 scripts/hil_evidence_packet_gate.py --packet-dir /tmp/run_20260511T150000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`：exit 0，`status=hil_pass`。
- `python3 -m py_compile scripts/evidence_crosscheck.py`：exit 0。

## 硬件结论

- Vendor 来源确认：WAVE ROVER UART 使用 newline-delimited JSON；`T=1001` 是 base feedback；`T=131` 开启反馈流；`T=142` 设置反馈间隔；`T=143` 控制 UART echo。
- 当前本机无真实 WAVE ROVER/串口候选；`hardware_smoke_wave_rover.py --status` 只能说明 readiness，被标记为 `software_proof`。
- `/tmp` synthetic fixture 输出 `status=hil_pass` 只是 gate 逻辑验证，不是实车证据，不得写入 OKR 为真实 HIL 完成。

## 剩余风险和下一步

- 需要真实 WAVE ROVER、现场确认串口设备、Docker `--device=<real_serial_device>` 透传后运行 `hardware_smoke_wave_rover.py --move-test`。
- 实车 run 后归档六个必需文件，再运行 `python3 scripts/hil_evidence_packet_gate.py --packet-dir evidence/<evidence_ref>`。
- 真实 packet gate 通过后，再用相同 `evidence_ref` 连接 O2/O3 crosscheck。
