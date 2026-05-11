# Sprint 2026.05.11_23-24 HIL Packet Crosscheck Bridge - Side2Side Check

## 对照结论

- 时间：2026-05-11 23:23 Asia/Shanghai
- 对照对象：`tech-plan.md` 的 HIL gate bridge 验收口径。
- 结论：软件 bridge 验收通过；真实 HIL 仍 blocked by environment/hardware absence。

## 需求对照

| 验收点 | 结果 | 证据 |
| --- | --- | --- |
| 新增 `--hil-gate-output <path>` | 通过 | `python3 scripts/evidence_crosscheck.py --help` 显示该参数 |
| `hil_pass` 且同 `evidence_ref` 才通过 | 通过 | `hil_pass_same_ref.json` exit 0，`CHECK summary: mismatches=0` |
| `blocked` 必须非 0 | 通过 | `blocked.json` exit 1，输出 `blocked (packet_dir_missing)` |
| `software_proof` 必须非 0 | 通过 | `software_proof.json` exit 1，输出 `software proof only` |
| `hil_pass` 但不同 `evidence_ref` 必须非 0 | 通过 | `hil_pass_wrong_ref.json` exit 1，输出 evidence_ref mismatch |
| 缺 gate 时保留软件复账 | 通过 | 无 `--hil-gate-output` exit 0，但输出 `software proof only` 边界 |
| 缺文件、不可解析、缺 `evidence_ref` 不得通过 | 通过 | 三个补充边界均 exit 1 |

## 用户验收边界

- 可以把本轮结果视为：O3/O2 crosscheck 已能消费 O1 HIL gate 输出，并阻止 blocked/software-only 证据冒充真实 HIL。
- 不可以把本轮结果视为：真实 WAVE ROVER 已上车通过、真实 `hil_pass` 已产生，或 OKR O1/O3 已因本轮完成而升级。
