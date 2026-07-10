# O1 WAVE ROVER Nonzero Feedback HIL Gate Side-by-side Check

## 用户价值和产品北极星

本轮对齐的用户价值是：在真实上车前，先把“WAVE ROVER 是否给出可信 nonzero 轮速反馈、是否满足 HIL 准入前置条件”收敛成可复现、可审计、fail-closed 的软件证据链，避免把混合坏日志、假阳性 payload 或 mock 样本误判成可控底盘。

## 对照检查

### 计划口径

- 只推进 O1，不把 local/mock wrapper 误记成 O5/O6/O7 增量。
- 产出一个可执行的 nonzero feedback gate，复用 vendor `T=1001` 解析。
- 证据边界固定为 software proof，不宣称真实 nonzero L/R，不宣称 HIL pass。
- 对坏输入 fail-closed，任何 invalid feedback line 都不能让顶层通过。

### 实际结果

- `wave_rover_nonzero_feedback_gate.py` 已落地，复用 `wave_rover_feedback.py` 的 vendor `T=1001` parser，支持 `feedback_T1001.log` 与 `--feedback-sample-json`。
- 输出固定 `source=software_proof`、`evidence_boundary=software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`、`hil_pass=false`、`safe_to_control=false`。
- 首轮验收发现 mixed bad JSON + nonzero `T=1001` 仍返回成功；返工后已收紧为任意 invalid feedback line 一律顶层 `status=blocked_invalid_feedback`，CLI `exit 4`，非 `T=1001` 行仍 ignored。
- 测试新增并通过：`python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*wave*rover*.py'` 输出 `Ran 9 tests in 0.005s OK`。
- 硬件文档已同步：`docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`。

## 验收判断

- **继续 O1，保守收口通过。**
- 本轮满足“建立 fail-closed nonzero feedback HIL gate 软件证据链”的目标，因此支持 O1 从约 85% 保守上调到约 86%。
- 本轮**不**满足“真实 WAVE ROVER nonzero L/R 已获取”或“真实 HIL pass 已发生”，因此不得把 `hil_pass`、`safe_to_control`、`delivery_success` 等字段上调为真。

## 证据边界

- 已验证：
  - vendor `T=1001` parser 复用成立；
  - nonzero feedback gate 能处理 mock/sample/log 输入；
  - mixed invalid feedback 会 fail-closed；
  - 测试与 scoped `git diff --check` 通过。
- 未验证：
  - 真实 WAVE ROVER 上车 nonzero L/R；
  - 真实轮向与真实运动观察一致性；
  - 同 run motion command、operator report、HIL acceptance record；
  - 真实 safe-to-control 或 HIL pass。

## 下一步

1. 在真实 WAVE ROVER 上车 run 中采集同一轮的 `feedback_T1001.log`、motion command record、operator report 和 HIL acceptance record。
2. 用本轮 gate 直接消费真实日志，确认是否出现可信 nonzero L/R 与方向模式。
3. 只有真实 run 证据齐备时，才允许继续提升 O1 或改变 `hil_pass=false` / `safe_to_control=false`。
