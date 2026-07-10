# O1 WAVE ROVER Nonzero Feedback HIL Gate Final

## 收口结论

本轮 Epic sprint 聚焦 O1“硬件协议可信底盘”的最低项缺口，完成了一个可执行、可复验、fail-closed 的 WAVE ROVER nonzero feedback HIL gate 软件证据链。产品判断为：**方向继续 O1，Objective 进度从约 85% 保守上调到约 86%**。上调依据不是实机运动或 HIL 通过，而是本轮把 vendor `T=1001` feedback 的 nonzero 判定、坏输入拦截、CLI 准入和文档边界固化成了后续真实上车可直接复用的 gate。

## 用户价值和产品北极星

产品北极星仍是“机器人可以安全、可验证地完成垃圾收取与送达”。本轮用户价值不在于再多一个 surface，而在于把“轮速反馈是否可信”“坏日志是否会误放行”“真实 HIL 前还缺哪些材料”变成可执行规则。这样下一次真实上车时，团队不会把一段看似有数据的日志误当成安全可控底盘。

## OKR 映射和方向判断

- Objective：O1 打通官方硬件协议，建立可信底盘控制层。
- 方向判断：**继续**。
- 进度调整：`~85% -> ~86%`。
- 调整理由：
  1. 新增 `wave_rover_nonzero_feedback_gate.py`，把 O1 的 software gate 从口头要求落成脚本、测试和硬件文档。
  2. 首轮暴露 mixed invalid feedback 漏口后已返工收紧，说明 gate 现在具备真正的 fail-closed 价值，而不是 happy path 样例。
  3. 证据边界仍严格保持 `software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`，没有越界声称真实 nonzero L/R 或 HIL pass。

## KR 状态

- 本轮**不归档** O1 KR。
- 本轮推进的是 O1 当前缺口中的“nonzero feedback / HIL 准入软件 gate”子项。
- O2/O3/O4 已归档项保持不动；O5/O6/O7 也不因本轮变化调整百分比或历史归档。

## 核心抓手与责任 Engineer

- 核心抓手：把 WAVE ROVER `T=1001` feedback 的 nonzero/HIL 准入判断做成 fail-closed gate。
- 责任 Engineer：`robot-hardware-engineer`。

## 验证与验收证据

- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*wave*rover*.py'`
  - `Ran 9 tests in 0.005s`
  - `OK`
- mixed invalid + nonzero CLI smoke：
  - 顶层结果：`status=blocked_invalid_feedback`
  - 退出码：`EXIT_CODE=4`
- 固定边界：
  - `source=software_proof`
  - `evidence_boundary=software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`
  - `hil_pass=false`
  - `safe_to_control=false`

## 风险、阻塞和需要补齐的证据链

1. 当前 nonzero 样本仍是 mock/sample/log 回放，不是实机 run。
2. `direction_summary` 只是 `L/R` 符号模式，不等于真实前进/后退/转向已经完成履约确认。
3. 仍缺同一真实 run 的：
   - `feedback_T1001.log`
   - motion command record
   - operator report 或外部运动观察材料
   - HIL acceptance record
4. 在这些材料到位前，O1 不能宣称真实 WAVE ROVER nonzero L/R、真实轮向确认、真实 safe-to-control 或真实 HIL pass。

## 对 CEO 的下一步建议

下一轮 O1 若要继续增长，必须切到真实上车证据采集 lane，而不是继续围绕 software gate 做包装。优先动作是拿同一 run 的真实 `feedback_T1001.log`、命令记录和 HIL acceptance record，让本轮 gate 直接消费真实材料并给出同 task 的准入判断。
