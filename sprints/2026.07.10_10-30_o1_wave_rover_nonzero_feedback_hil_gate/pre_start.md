# O1 WAVE ROVER Nonzero Feedback HIL Gate Pre-start

## sprint_type

sprint_type: epic

## 背景

本轮自动化已读取 `AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md` 与近期 O1/O5 相关 sprint 记录。当前 `OKR.md` 4.1 的最低 Objective 为 O1 / O5，二者均约 85%。

近期方向事实：

- O5 最近多轮已经把 local/mock probe、SQLite shadow、same-task readback、mission credit gate 做到回归守护上限；在没有真实 production cloud、production DB/queue、公网 HTTPS/TLS、4G/SIM 或 live endpoint 外部证据时，不能继续靠 wrapper/readback/checklist 提升 O5 百分比。
- O1 最近没有被连续 sprint 消费，但主要缺口仍明确：真实 WAVE ROVER `T1001` 轮速原始反馈仍未拿到 nonzero L/R，尚缺轮速方向确认、HIL 准入和 PR #5 硬件材料。
- `docs/vendor/VENDOR_INDEX.md` 已明确 WAVE ROVER 上下位机链路事实来源：UART、UTF-8 JSON newline framing、默认 `115200`、速度控制 `T=1` / `T=13`、反馈请求 `T=130`、反馈流 `T=131`。本轮只允许基于这些本地 vendor 资料规划可验证软件证据链，不得凭记忆扩展硬件细节。

## 本轮目标 Objective

- 主目标：O1 硬件协议可信底盘。
- 本轮目标不是宣称真实轮速 nonzero 或真实 HIL 通过，而是为 `robot-hardware-engineer` 建立一个可执行、fail-closed、可用 mock/虚拟串口验证的软件证据链，专门围绕 WAVE ROVER 非零 L/R 反馈采集与 HIL 准入前置条件。
- O5 本轮不推进百分比，只保留既有回归守护结论。

## 同一 blocker 避免

本轮主动避开 O5 已连续消费的同类 blocker：

- 无真实 production cloud / production DB/queue / live endpoint 外部材料。
- local/mock probe wrapper 只能证明 support-only，不能再贡献 O5 主 OKR 增量。

本轮切到 O1，但仍明确不重复消费 O1 的“必须现场拿到真实 nonzero L/R” blocker；处理方式是先把采集、fail-closed 判定、mock/虚拟串口验证和 HIL 准入门槛的软件工具链补齐，为下一次真实上车拿证据做准备。

## Owner

- `robot-hardware-engineer`：单线闭环负责后续实现、测试、修复和 `tech-done.md` 留档。
- `product-okr-owner`：仅负责本轮 Epic 计划文档，不进入实现，不修改 `OKR.md` 或收口文档。

## 验收口径

- 计划必须把 WAVE ROVER 反馈链路的软件目标写清：
  - 非零 L/R 反馈采集脚本或测试入口存在；
  - 缺真实硬件时可通过 mock/虚拟串口复现 vendor JSON feedback；
  - 对缺字段、零值、task 外输入或 unsafe payload fail-closed；
  - HIL 准入输出只能是 ready/not-ready 软件判定，不得把本轮结果写成 `safe_to_control=true`。
- 本轮计划证据边界固定为：
  - `software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`
  - not true WAVE ROVER nonzero L/R feedback
  - not HIL pass
  - not safe_to_control
