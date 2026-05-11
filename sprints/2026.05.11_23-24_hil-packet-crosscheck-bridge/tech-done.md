# Sprint 2026.05.11_23-24 HIL Packet Crosscheck Bridge - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-11 23:22 Asia/Shanghai
- Owner：`robot-software-engineer`
- 结论：`scripts/evidence_crosscheck.py` 已接入 HIL gate JSON output；bridge logic ready，真实 `hil_pass` 仍 pending。

## 实际改动

- `scripts/evidence_crosscheck.py`
  - 新增 `--hil-gate-output <path>` CLI 参数。
  - 读取 `scripts/hil_evidence_packet_gate.py` 保存后的 JSON output。
  - 将 `status=hil_pass` 且 `evidence_ref` 与 route/task run 一致作为 real-run aligned 的必要条件。
  - 将 `status=blocked`、`status=software_proof`、未知 status、gate 文件缺失、JSON 不可解析、payload 非对象、缺 `evidence_ref` 都纳入 mismatch 并返回非 0。
  - 未提供 `--hil-gate-output` 时，保留原 route/replay/task record software proof crosscheck 行为，并输出 `route/task alignment remains software proof only`。

## Gate Output 字段映射

- `status`：消费 `hil_pass`、`blocked`、`software_proof`；只有 `hil_pass` 可进入 real-run aligned 通过路径。
- `evidence_ref`：必须存在，并与 route status 派生的 run `evidence_ref` 一致。
- `blocked_reason` / `failures`：在 `blocked` 或 `software_proof` mismatch 中输出为失败定位。

## 验证结果

临时 fixture 路径：`/tmp/rober_hil_crosscheck_bridge`。其中 synthetic `hil_pass` 仅验证 bridge logic，不是实车证据。

- `python3 -m py_compile scripts/evidence_crosscheck.py`：exit 0。
- `python3 scripts/evidence_crosscheck.py --help`：exit 0，help 中出现 `--hil-gate-output HIL_GATE_OUTPUT`。
- `hil_pass_same_ref.json`：
  - 命令：`python3 scripts/evidence_crosscheck.py /tmp/rober_hil_crosscheck_bridge/route_status.json --task-record /tmp/rober_hil_crosscheck_bridge/task_record.json --hil-gate-output /tmp/rober_hil_crosscheck_bridge/hil_pass_same_ref.json`
  - 结果：exit 0；输出包含 `PASS hil_gate_output.status: 'hil_pass'`、`PASS hil_gate_output.evidence_ref == run evidence_ref`、`CHECK summary: mismatches=0`。
- `blocked.json`：
  - 结果：exit 1；输出包含 `FAIL hil_gate_output.status: blocked (packet_dir_missing)`、`CHECK summary: mismatches=1`。
- `software_proof.json`：
  - 结果：exit 1；输出包含 `FAIL hil_gate_output.status: software proof only (software_proof_allowed_status_only_packet)`、`CHECK summary: mismatches=1`。
- `hil_pass_wrong_ref.json`：
  - 结果：exit 1；输出包含 `FAIL hil_gate_output.evidence_ref == run evidence_ref`、`CHECK summary: mismatches=1`。
- 无 HIL gate software proof fixture：
  - 命令：`python3 scripts/evidence_crosscheck.py /tmp/rober_hil_crosscheck_bridge/route_status.json --task-record /tmp/rober_hil_crosscheck_bridge/task_record.json`
  - 结果：exit 0；输出包含 `INFO hil_gate_output not provided: route/task alignment remains software proof only`、`CHECK summary: mismatches=0`。
- 补充边界：
  - gate 文件缺失：exit 1；输出包含 `hil_gate_output not found`。
  - gate JSON 不可解析：exit 1；输出包含 `hil_gate_output: invalid JSON`。
  - gate 缺 `evidence_ref`：exit 1；输出包含 `FAIL hil_gate_output.evidence_ref: missing`。

## 失败定位

- 未出现实现范围内的意外失败。
- 非 0 分支均为预期失败，用于证明 blocked、software proof only、wrong evidence_ref 和坏 gate input 不会被误判成 real-run aligned。

## 剩余风险

- 当前本机没有真实 WAVE ROVER 串口和实车 run packet；本轮不能声明真实 HIL 通过。
- `/tmp` synthetic `hil_pass` fixture 只能证明 `evidence_crosscheck.py` bridge logic，不代表 O1/O3/O2 实机完成。
- 真实升级仍需要同一 `evidence_ref` 下的 HIL packet、fixed-route replay 和 task record。
