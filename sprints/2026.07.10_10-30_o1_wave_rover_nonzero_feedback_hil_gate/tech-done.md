# O1 WAVE ROVER Nonzero Feedback HIL Gate Tech Done

## 实际改动

1. 新增 `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_nonzero_feedback_gate.py`：
   - 复用 `wave_rover_feedback.py` 的 `parse_feedback_line()` 解析 vendor `T=1001`。
   - 支持 `feedback_T1001.log` 或 `--feedback-sample-json` 输入。
   - 输出固定 `source=software_proof`、`evidence_boundary=software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`、`hil_pass=false`、`safe_to_control=false`。
   - 对合法 `T=1001`、同帧 `L/R` 非零、`L/R` 符号模式摘要、缺失 HIL 材料做 fail-closed summary。
   - 本次返工把 mixed log 中的 invalid feedback line 提升为顶层 blocker：任意 bad JSON、缺字段、非 object 或非法 `T=1001` payload 都会让顶层 `status=blocked_invalid_feedback`，CLI 非 0；非 `T=1001` 行仍只记为 ignored。
2. 更新 `onboard/src/ros2_trashbot_hardware/setup.py`：
   - 新增 console script `wave_rover_nonzero_feedback_gate`。
3. 新增 `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_nonzero_feedback_gate.py`：
   - 覆盖 positive nonzero、all-zero blocked、bad JSON blocked、缺字段 blocked、非 `T=1001` ignored、wrapper log mixed invalid+nonzero blocked、CLI success/block exit code。
4. 新增 `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`：
   - 记录 vendor 来源、software proof 边界、fail-closed 规则和真实 HIL 仍缺材料。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/hardware/wave_rover_json_bridge.md`

已采用的硬件结论：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001`。
- `T=1001` base feedback 需要 `L/R/r/p/y/v` 同帧齐备才承认。
- 本轮 gate 只总结 `L/R` 符号模式，不把 mock/日志结果升级为真实轮向或真实 HIL 通过。

## 验证结果

1. `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_nonzero_feedback_gate.py`
   - 结果：通过，无输出。
2. `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*wave*rover*.py'`
   - 结果：`Ran 9 tests in 0.005s`，`OK`。
3. `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*hardware*.py'`
   - 结果：`Ran 10 tests in 0.006s`，`OK`。
4. `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_nonzero_feedback_gate --feedback-sample-json '{"T":1001,"L":61,"R":-61,"r":0.2,"p":0.1,"y":0,"v":11.8}'`
   - 结果：输出 `status=software_proof_nonzero_lr_observed`，`direction_summary.left_positive_right_negative=1`，同时固定 `hil_pass=false`、`safe_to_control=false`。
5. `git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate`
   - 结果：通过，无 whitespace / conflict marker 问题。
6. mixed invalid+nonzero CLI smoke：
   - 输入：同一 `feedback_T1001.log` 内同时包含 `not json at all` 和一个合法 nonzero `T=1001` wrapper payload。
   - 结果：输出 `status=blocked_invalid_feedback`，保留 `paired_nonzero_count=1`、`direction_summary.both_positive=1`、`latest_nonzero_pair` 作为诊断信息，同时 `EXIT_CODE=4`。

## 失败定位

主会话验收发现首版 gate 的 fail-closed 漏口：mixed log 里只要存在一个合法 nonzero `T=1001`，顶层仍可能返回成功。根因是状态机把 `invalid_feedback_count > 0` 仅作为附加 blocker，而没有无条件压顶层 `status`。本次已修复为：任意 invalid feedback line 都直接把顶层锁到 `blocked_invalid_feedback`，同时保留 nonzero 诊断信息用于排障。

## 剩余风险

1. 当前 nonzero 样本来自 mock / fixture / log 回放，不是真实 WAVE ROVER 上车证据。
2. `direction_summary` 仅是 `L/R` 符号模式摘要，不等于现场已经验证真实前进、后退或转向。
3. 真实履约仍缺：
   - 同一 run 的真实 `feedback_T1001.log`
   - 同一 run 的 motion command record
   - 同一 run 的 operator report 或外部运动观察材料
   - 同一 run 的 HIL acceptance record
4. 在这些材料补齐前，必须保持 `source=software_proof`、`hil_pass=false`、`safe_to_control=false`，不能宣称真实 WAVE ROVER nonzero L/R 或 HIL pass。
